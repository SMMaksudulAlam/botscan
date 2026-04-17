import pandas as pd
from collections import Counter

file_path = "splited_data_on_family.xlsx"
xls = pd.ExcelFile(file_path)

all_ports = []

# ---- Per-family analysis ----
for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)

    ioc_values = df["ioc_value"].dropna().astype(str)

    port_counter = Counter()
    na_count = 0

    for val in ioc_values:
        try:
            ip, port = val.split(":")
            if port.upper() == "N/A":
                na_count += 1
                continue
            port_counter[port] += 1
            all_ports.append(port)
        except ValueError:
            continue

    total = sum(port_counter.values())

    if total == 0:
        print(f"\nSheet: {sheet} (No valid ports)")
        continue

    sorted_ports = sorted(port_counter.items(), key=lambda x: x[1], reverse=True)

    top_port, top_count = sorted_ports[0]
    top_percentage = (top_count / total) * 100

    print(f"\n===== {sheet.upper()} =====")
    print(f"Total valid port interactions: {total}")
    print(f"Entries with N/A port: {na_count}")
    print(f"Most popular port: {top_port}")
    print(f"Count: {top_count}")
    print(f"Percentage: {top_percentage:.2f}%")

    def coverage(k):
        return sum(count for _, count in sorted_ports[:k]) / total * 100

    for k in [50, 500, 1000]:
        print(f"Top {k} ports cover: {coverage(k):.2f}%")

# =========================
# Combined Analysis
# =========================

combined_counter = Counter(all_ports)
total_all = sum(combined_counter.values())

sorted_ports_all = sorted(combined_counter.items(), key=lambda x: x[1], reverse=True)

top_port_all, top_count_all = sorted_ports_all[0]
top_percentage_all = (top_count_all / total_all) * 100

print("\n=========================")
print("COMBINED ANALYSIS")
print("=========================")
print(f"Total valid port interactions: {total_all}")
print(f"Most popular port: {top_port_all}")
print(f"Count: {top_count_all}")
print(f"Percentage: {top_percentage_all:.2f}%")

def coverage_all(k):
    return sum(count for _, count in sorted_ports_all[:k]) / total_all * 100

for k in [50, 500, 1000]:
    print(f"Top {k} ports cover: {coverage_all(k):.2f}%")