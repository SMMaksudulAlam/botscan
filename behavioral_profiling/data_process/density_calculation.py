import re
import pandas as pd
from collections import Counter
from ipaddress import ip_network, ip_address

X = "splited_data_on_family"
file_path = f"{X}.xlsx"
xlsx = pd.ExcelFile(file_path)

subnet_concentration_stats = {}

# Global collector
all_ips_global = []

# CIDR granularities
CIDR_PREFIXES = [32, 31, 28, 24, 20, 16, 12, 8, 0]

# IPv4 regex
_IPV4_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def extract_ipv4s(value: str):
    """Return a list of valid IPv4s found inside the string."""
    if not isinstance(value, str):
        return []
    candidates = _IPV4_RE.findall(value)
    valid = []
    for c in candidates:
        parts = c.split('.')
        if all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            try:
                ip_address(c)
                valid.append(c)
            except Exception:
                continue
    return valid


def average_prefix_concentration_by_cidr(ip_list, prefix_len: int) -> float:
    """
    Average density (%) across observed /prefix_len networks:
    """
    if not (0 <= prefix_len <= 32):
        raise ValueError("prefix_len must be between 0 and 32.")

    prefix_counts = Counter()

    for ip in ip_list:
        try:
            net = ip_network(f"{ip}/{prefix_len}", strict=False)
            prefix_counts[f"{net.network_address}/{prefix_len}"] += 1
        except Exception:
            continue

    if not prefix_counts:
        return 0.0

    ips_per_network = 2 ** (32 - prefix_len)
    total_ips = sum(prefix_counts.values())
    num_networks = len(prefix_counts)

    avg_density = (total_ips * 100.0) / (num_networks * ips_per_network)
    return round(avg_density, 6)


# ---- Main Loop ----
for sheet in xlsx.sheet_names:
    print(f"Processing: {sheet}")

    df = xlsx.parse(sheet, usecols=["ioc_value"]).dropna(subset=["ioc_value"])

    # Extract IPs
    ip_series = df["ioc_value"].astype(str).apply(extract_ipv4s)
    ip_list = [ip for lst in ip_series for ip in lst]

    # De-duplicate per sheet
    unique_ip_list = sorted(set(ip_list))

    # accumulate globally (frequency-aware; better for density realism)
    all_ips_global.extend(ip_list)

    if ip_list:
        print(f"  Found {len(ip_list)} IPv4s; {len(unique_ip_list)} unique.")

    # Compute locality per sheet
    subnet_concentration_stats[sheet] = {
        f"/{p}": average_prefix_concentration_by_cidr(unique_ip_list, p)
        for p in CIDR_PREFIXES
    }


# ---- GLOBAL ANALYSIS ----
print("\nProcessing: GLOBAL DATASET")

global_unique_ips = sorted(set(all_ips_global))

global_stats = {
    f"/{p}": average_prefix_concentration_by_cidr(global_unique_ips, p)
    for p in CIDR_PREFIXES
}

subnet_concentration_stats["GLOBAL"] = global_stats


# ---- Save Output ----
subnet_df = pd.DataFrame.from_dict(subnet_concentration_stats, orient="index")

output_file = "subnet_locality_analysis_on_family.xlsx"

with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    subnet_df.to_excel(writer, sheet_name="Subnet_Locality")

print("✅ Analysis complete. Output saved to:", output_file)