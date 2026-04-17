import pandas as pd

# Load the Excel file
file_path = "splited_data_on_family.xlsx"
xls = pd.ExcelFile(file_path)

# Sheet names
sheets = ["mirai", "gafgyt", "mozi", "hajime", "kaiji"]

all_ioc_values = []

for sheet in sheets:
    df = pd.read_excel(xls, sheet_name=sheet)

    ioc_values = df["ioc_value"].dropna().astype(str)

    all_ioc_values.extend(ioc_values.tolist())

    total_count = len(ioc_values)
    unique_ip_port = set(ioc_values)

    ips = set()
    ports = set()
    na_ip_count = 0
    na_ips = set()

    for val in unique_ip_port:
        try:
            ip, port = val.split(":")
            ips.add(ip)

            if port.upper() == "N/A":
                na_ip_count += 1
                na_ips.add(ip)
            else:
                ports.add(port)

        except ValueError:
            continue

    print(f"\nSheet: {sheet}")
    print(f"Total IP:Port count: {total_count}")
    print(f"Unique IP:Port count: {len(unique_ip_port)}")
    print(f"Unique IP count: {len(ips)}")
    print(f"Unique port count (excluding N/A): {len(ports)}")
    print(f"IPs with no port (N/A): {len(na_ips)}")

# =========================
# Combined Statistics
# =========================

all_ioc_values = pd.Series(all_ioc_values).dropna().astype(str)

total_count_all = len(all_ioc_values)
unique_ip_port_all = set(all_ioc_values)

ips_all = set()
ports_all = set()
na_ips_all = set()

for val in unique_ip_port_all:
    try:
        ip, port = val.split(":")
        ips_all.add(ip)

        if port.upper() == "N/A":
            na_ips_all.add(ip)
        else:
            ports_all.add(port)

    except ValueError:
        continue

print("\n=========================")
print("Combined Statistics")
print("=========================")
print(f"Total IP:Port count: {total_count_all}")
print(f"Unique IP:Port count: {len(unique_ip_port_all)}")
print(f"Unique IP count: {len(ips_all)}")
print(f"Unique port count (excluding N/A): {len(ports_all)}")
print(f"IPs with no port (N/A): {len(na_ips_all)}")