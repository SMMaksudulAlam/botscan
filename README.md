## Artifact Overview

This repository contains the code and artifacts used in our experiments for
identifying and probing C2 servers using active malware execution and
replay-based probing. Due to platform limitations and security considerations,
some datasets and artifacts are partially shared or summarized.

## A note on Evaluation 1

Active probing in practice depends on the target IP space, live-host
availability, and the replay signatures available at probing time. For
convenience of evaluation, we separate the system into two independently
provided parts: the **scanner** (`scanner_tool/`) and the **behavior-adaptive
target selector** (`behavior_adaptive_algorithm/`).

In our work, the Evaluation 1 target space was measured with the complete end-to-end BotScan
system (active port discovery + adaptive replay-based active probing), producing the live C2
outcomes. However, the evidence shown in the artifact is an **offline replay
of that completed measurement**: each policy (BotScan and the comparable baselines) selects
its next target using its own algorithm, and a target is counted as a hit if it
appears in the shared list of C2 IPs detected in that earlier active-probing
phase. Please note that **no malicious packets are sent by the notebook**, but the other required info, i.e., metadata of target-space, AS info, etc., is still crawled from the internet at runtime for adaptive ranking. We do this purposefully for reproducibility
(anyone can re-run it without Internet-wide probing), fairness among policies on the same context (replaying all
policies against one fixed outcome set removes live-host availability and flaky
C2 responsiveness as a confound, so differences reflect the selection strategy
itself), and to avoid any security concerns. After acceptance, we will release the integrated end-to-end package that 
connects BotScan's scanner to its adaptive selector.

## Directory Structure

- **`scanner_tool/`** — the scanner used in active probing.
  - `scaled_replay`: given a segment, probes all IPs in that segment.
  - `map_probe`: loads the payload data and prepares it for the scanner.
- **`behavior_adaptive_algorithm/`** — behavior-adaptive target-selection
  algorithm (Evaluation 1). Contains the seed IPs and the C2 IPs detected in the
  earlier real-life active scanning, plus the notebook that replays BotScan and
  the baseline selection policies against them. The scanner is kept in a
  separate directory for organization.
- **`behavioral_profiling/`** — collates data from different sources to build
  BP-DS and analyzes it for the locality/port-usage insights, including the
  historical parameter sweep supporting the choice of K = 10, lambda = 2.0.
- **`malware_network_traces_extract_analysis/`** — scripts and notebooks for
  extracting and analyzing network traces from malware execution.
- **`thought_experiment/`** — Evaluation 2, the large-scale retrospective
  emulation on historical data. `validation_2.ipynb` reproduces the experiment
  and analysis.
- **`pcap_samples/`** — example PCAPs from active malware execution. Due to size
  and platform upload limits, only a subset is shared.
- **`resource_consumption_measurement/`** — data and scripts comparing resource
  consumption between activation-based and replay-based probing (Table 3 /
  Appendix I).
- **`result_verification_with_VT/`** — code to verify results via the
  VirusTotal API (Appendix J).
- **`spatial_experiment_result_snapshot/`** — data and intermediate results for
  the spatial (Case Study 1) analysis.
- **`temporal_experiment_result_snapshot/`** — data and intermediate results for
  the temporal (Case Study 2) analysis.
- **`Experimental_Results.xlsx`** — summary of experimental results reported in
  the paper.

## Notes on Data and Malware Availability

For security and safety reasons, malware binaries used in our experiments are
not shared as part of this artifact. Instead, we provide network traces,
extracted features, and analysis results sufficient to reproduce and validate
our findings without distributing live malware.

Additionally, some large datasets, such as full PCAP traces generated during
malware execution, cannot be fully shared due to platform size limitations.
Where applicable, representative samples and processed results are provided.
