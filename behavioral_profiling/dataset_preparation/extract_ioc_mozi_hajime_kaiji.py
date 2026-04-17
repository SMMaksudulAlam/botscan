import re
import pandas as pd

# Input files
files = {
    "mozi": "mozi.txt",
    "hajime": "hajime.txt",
    "kaiji": "kaiji.txt"
}

# Regex patterns
pattern_with_port = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})\b')
pattern_ip_only = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b')

# Output Excel file
output_file = "extracted_iocs.xlsx"

with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    
    for family, file_path in files.items():
        ioc_set = set()

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                
                # First extract IP:Port
                matches_with_port = pattern_with_port.findall(line)
                for ip, port in matches_with_port:
                    ioc_set.add(f"{ip}:{port}")

                # Then extract IP-only
                matches_ip_only = pattern_ip_only.findall(line)
                for ip in matches_ip_only:
                    # Check if this IP already has a port entry
                    if not any(entry.startswith(ip + ":") for entry in ioc_set):
                        ioc_set.add(f"{ip}:N/A")

        # Convert to DataFrame
        df = pd.DataFrame(sorted(ioc_set), columns=["ioc_value"])

        # Write to sheet
        df.to_excel(writer, sheet_name=family, index=False)

print(f"Excel file created: {output_file}")