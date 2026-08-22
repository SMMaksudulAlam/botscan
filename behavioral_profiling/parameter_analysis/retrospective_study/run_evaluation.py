"""BotScan (K=10, lambda=2.0) vs. Baseline 1 vs. Baseline 2 on the
thought-experiment C2 corpus (103.0.0.0/8-scoped ThreatFox export).

Algorithm code (Oracle, ScoreBoard, run_botscan, run_baseline1, run_baseline2,
cost model) is a direct, line-for-line port of
`Evaluation 1/botscan_evaluation_1_finalized_remaned.ipynb`, with one
deliberate fix: `run_baseline2`'s `set(all_segs) - set(probed)` (hash-order
dependent, non-reproducible across Python processes) is replaced with a
list comprehension that preserves a fixed order. Everything else is
unchanged, including the exact seed-cost/segment-cost model and the W1/W2
ScoreBoard weights.

Candidate graph: built entirely from already-fetched, real WHOIS/RADB data
(`data/filtered_103_prioritized_with_prefixes.xlsx`, produced by
`thought_experiment/validation_2.ipynb` cells 0-7 via `whois.radb.net`
`-i origin ASxxxx` queries). No network calls are made by this script -- see
REPORT.md for why a fresh live fetch over the full corpus was judged
infeasible and why this scope was chosen instead.

Run: python3 run_evaluation.py
"""
import ipaddress
import random
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Cost model and ScoreBoard weights -- identical to Evaluation 1's notebook
# ---------------------------------------------------------------------------
AVG_PORTS_PER_IP = 15
COST_PER_SEGMENT = 256 * AVG_PORTS_PER_IP     # 3,840 IP:port per /24
MAX_BUDGET = 1_000_000
W1, W2 = 10.0, 100.0
K, LAM = 10, 2.0                              # tuned params from Evaluation_4
RANDOM_SEED = 42

CHECKPOINTS = [20_000, 112_000, 225_000, 550_000]

DATA_XLSX = "data/filtered_103_prioritized_with_prefixes.xlsx"

# Seed IPs: the same 19 unique seed IPs used throughout thought_experiment/
# (validation_2.ipynb's BotScan / AutoProbe cells), all status "L" (live --
# confirmed ThreatFox detections used as the initial evidence set).
SEED_IPS = [
    "103.136.41.111", "103.149.87.111", "103.153.69.151", "103.162.29.212",
    "103.166.184.95", "103.173.255.143", "103.178.229.220", "103.179.188.48",
    "103.181.56.118", "103.195.236.98", "103.217.116.211", "103.237.87.90",
    "103.41.25.179", "103.82.25.131", "103.153.69.114", "103.161.17.72",
    "103.178.232.12", "103.82.22.249", "103.91.245.13",
]


def ip_to_subnet(ip_str):
    ip = ipaddress.ip_address(ip_str)
    return str(ipaddress.ip_network(f"{ip}/24", strict=False))


def normalize_asn(asn_value):
    if pd.isna(asn_value):
        return None
    s = str(asn_value).strip()
    if s.upper().startswith("AS"):
        s = s[2:].strip()
    if "." in s:
        s = s.split(".", 1)[0]
    return s if s else None


# ---------------------------------------------------------------------------
# Load data and build ground truth + candidate graph
# ---------------------------------------------------------------------------
def load_ground_truth_and_graph():
    df = pd.read_excel(DATA_XLSX)
    df["ip"] = df["ip"].astype(str)
    df["asn_norm"] = df["asn"].apply(normalize_asn)

    all_ips = set(df["ip"]) | set(SEED_IPS)
    assert set(SEED_IPS) <= set(df["ip"]), "seed IPs must be part of the ground-truth corpus"

    ip_asn = dict(zip(df["ip"], df["asn_norm"]))

    ground_truth_pool = defaultdict(list)
    for ip in df["ip"]:
        ground_truth_pool[ip_to_subnet(ip)].append(ip)

    # asn -> exact-/24-announced prefixes (real RADB route/route6 records,
    # filtered to IPv4 /24s -- same filter Evaluation 1 applies to its
    # bgp.tools/bgpview/RIPEstat fetch: `[p for p in prefs if p.endswith("/24")]`)
    asn_prefixes = defaultdict(set)
    for asn, raw in zip(df["asn_norm"], df["asn_prefixes"]):
        if not asn or pd.isna(raw):
            continue
        for p in str(raw).split(","):
            p = p.strip()
            if not p:
                continue
            try:
                net = ipaddress.ip_network(p, strict=False)
            except ValueError:
                continue
            if net.version == 4 and net.prefixlen == 24:
                asn_prefixes[asn].add(str(net))

    evidence_subnets = {ip_to_subnet(ip) for ip in all_ips}

    candidate_subnets = set()
    for prefs in asn_prefixes.values():
        candidate_subnets.update(prefs)
    candidate_subnets.update(evidence_subnets)

    # subnet -> owning ASN (announced prefix first, evidence-IP fallback --
    # same precedence as Evaluation 1's build_graph).
    #
    # NOTE: candidate_subnets / evidence_subnets / asn_prefixes are Python
    # `set`/`dict`-of-sets built from string keys, whose iteration order is
    # PYTHONHASHSEED-dependent (randomized per process by default). Iterating
    # them directly would make `subnet_asn`'s insertion order -- and hence
    # `all_segments` below, and hence every rng.choice()/ScoreBoard.top()
    # tie-break downstream -- silently different on every run. Every such
    # iteration is sorted so the whole pipeline is reproducible given the
    # same random_seed.
    subnet_asn = {}
    for sn in sorted(candidate_subnets):
        owner = next((asn for asn, prefs in sorted(asn_prefixes.items()) if sn in prefs), None)
        if owner is None:
            owner = next((ip_asn[ip] for ip in sorted(ip_asn) if ip_to_subnet(ip) == sn), None)
        if owner:
            subnet_asn[sn] = owner
    for sn in sorted(evidence_subnets):
        if sn not in subnet_asn:
            owner = next((ip_asn[ip] for ip in sorted(ip_asn) if ip_to_subnet(ip) == sn), None)
            if owner:
                subnet_asn[sn] = owner
        if sn not in subnet_asn:
            subnet_asn[sn] = f"UNKNOWN_{sn}"   # evidence with no resolvable ASN: isolated segment

    as_to_segs = defaultdict(list)
    for sn, asn in subnet_asn.items():
        as_to_segs[asn].append(sn)
    for asn in as_to_segs:
        as_to_segs[asn] = sorted(as_to_segs[asn])

    seg_pos = {}
    for asn, segs in as_to_segs.items():
        for i, s in enumerate(segs):
            seg_pos[s] = (i, segs)

    all_segments = sorted(subnet_asn.keys())
    return ground_truth_pool, all_segments, seg_pos, all_ips


# ---------------------------------------------------------------------------
# Oracle / ScoreBoard -- verbatim from Evaluation 1
# ---------------------------------------------------------------------------
@dataclass
class ProbeResult:
    segment: str
    c2s_found: list
    cost: int
    already_probed: bool = False


class Oracle:
    def __init__(self, ground_truth_pool):
        self.ground_truth_pool = ground_truth_pool
        self._log = []
        self._probed = set()

    def probe(self, segment):
        if segment in self._probed:
            prior = next(r for r in self._log if r.segment == segment)
            return ProbeResult(segment, prior.c2s_found, 0, True)
        c2s = list(self.ground_truth_pool.get(segment, []))
        res = ProbeResult(segment, c2s, COST_PER_SEGMENT)
        self._log.append(res)
        self._probed.add(segment)
        return res


class ScoreBoard:
    def __init__(self, seg_pos, all_segs, K, lam):
        self.K, self.lam = K, lam
        self.seg_pos = seg_pos
        self.rint = {s: 0.0 for s in all_segs}
        self.rext = {s: 0.0 for s in all_segs}
        self._probed = set()

    def _propagate(self, seg, delta_rint, sign):
        if self.K == 0 or seg not in self.seg_pos:
            return
        idx, segs = self.seg_pos[seg]
        for j in range(1, self.K + 1):
            contribution = sign * delta_rint / (self.lam ** j) / (2 * self.K)
            for ni in (idx - j, idx + j):
                if 0 <= ni < len(segs):
                    nbr = segs[ni]
                    if nbr not in self._probed:
                        self.rext[nbr] += contribution

    def apply_seed(self, seg, detections, seeds_in_seg):
        old_rint = self.rint.get(seg, 0.0)
        self._propagate(seg, old_rint, -1)
        silent = max(0, seeds_in_seg - detections)
        new_rint = W2 * detections + W1 * silent
        self.rint[seg] = new_rint
        self._propagate(seg, new_rint, +1)

    def record_probe(self, seg, n_c2s, seeds_in_seg=0):
        self._probed.add(seg)
        old_rint = self.rint.get(seg, 0.0)
        self._propagate(seg, old_rint, -1)
        silent = max(0, seeds_in_seg - n_c2s)
        new_rint = W2 * n_c2s + W1 * silent
        self.rint[seg] = new_rint
        self._propagate(seg, new_rint, +1)

    def top(self):
        return max((s for s in self.rint if s not in self._probed), key=self.score_of)

    def score_of(self, seg):
        return self.rint.get(seg, 0.0) + self.rext.get(seg, 0.0)


# ---------------------------------------------------------------------------
# run_botscan / run_baseline1 / run_baseline2 -- verbatim from Evaluation 1,
# generalized to take ground_truth_pool/seg_pos explicitly instead of module
# globals, plus the run_baseline2 determinism fix noted at the top of the file.
# ---------------------------------------------------------------------------
def run_botscan(seed_entries, all_segs, ground_truth_pool, seg_pos,
                 budget=MAX_BUDGET, K=3, lam=1.0, r_explore=0.0, random_seed=42):
    detected = set()
    oracle = Oracle(ground_truth_pool)
    sb = ScoreBoard(seg_pos, all_segs, K=K, lam=lam)
    rng = random.Random(random_seed)
    curve = []

    seg_counts = defaultdict(lambda: {"seeds": 0, "live": 0})
    for row in seed_entries:
        seg = ip_to_subnet(row["ip"])
        seg_counts[seg]["seeds"] += 1
        if row["status"] == "L":
            seg_counts[seg]["live"] += 1

    seed_count = {seg: info["seeds"] for seg, info in seg_counts.items()}

    seed_cost = 0
    for seg, info in seg_counts.items():
        detections = info["live"]
        seeds_here = info["seeds"]
        seed_cost += seeds_here * AVG_PORTS_PER_IP
        for ip in ground_truth_pool.get(seg, []):
            if any(s["ip"] == ip and s["status"] == "L" for s in seed_entries):
                detected.add(ip)
        sb.apply_seed(seg, detections, seeds_here)

    curve.append((seed_cost, len(detected)))

    unexplored = list(all_segs)
    total_cost = seed_cost
    while unexplored and total_cost < budget:
        chosen = rng.choice(unexplored) if rng.random() < r_explore else sb.top()
        res = oracle.probe(chosen)
        total_cost += res.cost
        detected.update(res.c2s_found)
        seeds_here = seed_count.get(chosen, 0)
        sb.record_probe(chosen, len(res.c2s_found), seeds_in_seg=seeds_here)
        curve.append((total_cost, len(detected)))
        unexplored.remove(chosen)

    return curve


def run_baseline1(seed_entries, all_segs, ground_truth_pool, budget=MAX_BUDGET, random_seed=42):
    detected = set()
    oracle = Oracle(ground_truth_pool)
    rng = random.Random(random_seed)
    curve = []

    seg_counts = defaultdict(lambda: {"seeds": 0, "live": 0})
    for row in seed_entries:
        seg = ip_to_subnet(row["ip"])
        seg_counts[seg]["seeds"] += 1
        if row["status"] == "L":
            seg_counts[seg]["live"] += 1

    seed_cost = 0
    for seg, info in seg_counts.items():
        seed_cost += info["seeds"] * AVG_PORTS_PER_IP
        if info["live"] > 0:
            for ip in ground_truth_pool.get(seg, []):
                if any(s["ip"] == ip and s["status"] == "L" for s in seed_entries):
                    detected.add(ip)

    curve.append((seed_cost, len(detected)))

    remaining = list(all_segs)
    total_cost = seed_cost
    while total_cost < budget and remaining:
        seg = rng.choice(remaining)
        remaining.remove(seg)
        res = oracle.probe(seg)
        total_cost += res.cost
        detected.update(res.c2s_found)
        curve.append((total_cost, len(detected)))

    return curve


def run_baseline2(seed_entries, all_segs, ground_truth_pool, budget=MAX_BUDGET, random_seed=42):
    detected = set()
    oracle = Oracle(ground_truth_pool)
    rng = random.Random(random_seed)
    curve = []

    seg_counts = defaultdict(lambda: {"seeds": 0, "live": 0})
    for row in seed_entries:
        seg = ip_to_subnet(row["ip"])
        seg_counts[seg]["seeds"] += 1
        if row["status"] == "L":
            seg_counts[seg]["live"] += 1

    seed_cost = 0
    seed_segs = set()
    for seg, info in seg_counts.items():
        seed_cost += info["seeds"] * AVG_PORTS_PER_IP
        if info["live"] > 0:
            for ip in ground_truth_pool.get(seg, []):
                if any(s["ip"] == ip and s["status"] == "L" for s in seed_entries):
                    detected.add(ip)
        seed_segs.add(seg)

    curve.append((seed_cost, len(detected)))
    total_cost = seed_cost

    probed = set()
    for seg in sorted(seed_segs):
        if total_cost >= budget:
            break
        res = oracle.probe(seg)
        total_cost += res.cost
        detected.update(res.c2s_found)
        probed.add(seg)
        curve.append((total_cost, len(detected)))

    # Fix vs. the raw Evaluation 1 code: `list(set(all_segs) - set(probed))`
    # is hash-seed dependent (non-reproducible across processes). This list
    # comprehension is deterministic and order-preserving instead.
    remaining = [s for s in all_segs if s not in probed]

    while total_cost < budget and remaining:
        seg = rng.choice(remaining)
        remaining.remove(seg)
        res = oracle.probe(seg)
        total_cost += res.cost
        detected.update(res.c2s_found)
        curve.append((total_cost, len(detected)))

    return curve


def c2s_at(curve, target):
    best = 0
    for cost, n in curve:
        if cost <= target:
            best = n
    return best


def main():
    ground_truth_pool, all_segments, seg_pos, all_ips = load_ground_truth_and_graph()
    print(f"Ground-truth C2 IPs: {sum(len(v) for v in ground_truth_pool.values())}")
    print(f"Candidate /24 segments: {len(all_segments)}")
    print(f"Max explorable budget (all segments): {len(all_segments) * COST_PER_SEGMENT:,} IP:port "
          f"(run budget capped at {MAX_BUDGET:,})")

    seed_entries = [{"ip": ip, "status": "L"} for ip in SEED_IPS]

    print("\nRunning BotScan (K=%d, lambda=%.1f) ..." % (K, LAM))
    curve_bs = run_botscan(seed_entries, all_segments, ground_truth_pool, seg_pos,
                            budget=MAX_BUDGET, K=K, lam=LAM, r_explore=0.0,
                            random_seed=RANDOM_SEED)
    print(f"  -> {curve_bs[-1][1]} C2s @ {curve_bs[-1][0]:,} IP:ports")

    print("Running Baseline 1 (seeds, then random) ...")
    curve_b1 = run_baseline1(seed_entries, all_segments, ground_truth_pool,
                              budget=MAX_BUDGET, random_seed=RANDOM_SEED)
    print(f"  -> {curve_b1[-1][1]} C2s @ {curve_b1[-1][0]:,} IP:ports")

    print("Running Baseline 2 (seeds, seed /24s, then random) ...")
    curve_b2 = run_baseline2(seed_entries, all_segments, ground_truth_pool,
                              budget=MAX_BUDGET, random_seed=RANDOM_SEED)
    print(f"  -> {curve_b2[-1][1]} C2s @ {curve_b2[-1][0]:,} IP:ports")

    rows = []
    for x in CHECKPOINTS:
        rows.append({
            "ip_port_budget": x,
            "Baseline_1": c2s_at(curve_b1, x),
            "Baseline_2": c2s_at(curve_b2, x),
            "BotScan_K10_L2": c2s_at(curve_bs, x),
        })
    df_pts = pd.DataFrame(rows).set_index("ip_port_budget")
    print("\nCumulative C2s detected at each checkpoint:")
    print(df_pts.to_string())
    df_pts.to_csv("results_table.csv")

    for name, curve in [("botscan", curve_bs), ("baseline1", curve_b1), ("baseline2", curve_b2)]:
        pd.DataFrame(curve, columns=["cum_cost", "cum_c2s"]).to_csv(f"curve_{name}.csv", index=False)

    make_plot(df_pts)
    print("\nSaved: results_table.csv, curve_{botscan,baseline1,baseline2}.csv, comparison_barchart.png")


def make_plot(df_pts):
    # Uniform 27pt for axis labels, tick labels, bar value labels, and legend.
    FS = 27
    labels = [f"{x // 1000}K" for x in df_pts.index]
    methods = ["Baseline_1", "Baseline_2", "BotScan_K10_L2"]
    display_names = ["Baseline 1", "Baseline 2", "BotScan (K = 10, λ = 2)"]
    colors = ["#1f4e9c", "#2e9e4f", "#e8821e"]
    hatches = [None, "//", "//"]

    x = range(len(df_pts))
    width = 0.26
    fig, ax = plt.subplots(figsize=(16, 6))

    for i, (m, name, c, h) in enumerate(zip(methods, display_names, colors, hatches)):
        offs = (i - 1) * width
        vals = df_pts[m].values
        bars = ax.bar([xi + offs for xi in x], vals, width=width, label=name,
                      color=c, hatch=h, edgecolor="black", linewidth=0.6)
        ax.bar_label(bars, padding=3, fontsize=FS)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Explored IP:Port count", fontsize=FS)
    ax.set_ylabel("# of C2 Servers", fontsize=FS)
    ax.tick_params(axis="both", labelsize=FS)
    ax.legend(fontsize=FS, loc="upper left", frameon=True, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.1)
    fig.tight_layout()
    fig.savefig("comparison_barchart.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
