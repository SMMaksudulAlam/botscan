import requests
import pandas as pd
import time

API_KEY = ''
VT_URL = 'https://www.virustotal.com/api/v3/ip_addresses/'

def check_ip_status(ip):
    headers = {
        'x-apikey': API_KEY
    }
    try:
        response = requests.get(VT_URL + ip, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        data = response.json()
        attributes = data.get('data', {}).get('attributes', {})
        last_analysis_stats = attributes.get('last_analysis_stats', {})
        
        malicious_count = last_analysis_stats.get('malicious', 0) + last_analysis_stats.get('suspicious', 0)
        harmless_count = last_analysis_stats.get('harmless', 0)
        
        if malicious_count > 0:
            return "Y", malicious_count
        elif harmless_count > 0:
            return "Y", 0
        else:
            return "N", 0
    except Exception as e:
        print(f"Error while processing IP {ip}: {e}")
        return "Error", 0

def process_ip_file(file_path):
    results = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                try:
                    ip, port = line.strip().split()
                    print(ip, port)
                    scanned, count = check_ip_status(ip)
                    results.append([ip, port, scanned, count])
                    time.sleep(17)
                except ValueError as ve:
                    print(f"Error parsing line '{line.strip()}': {ve}")
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        df = pd.DataFrame(results, columns=['IP', 'Port', 'Scanned by VT', 'TE Count'])
        df.to_excel('ip_status_results.xlsx', index=False)
        print("Results written to ip_status_results.xlsx")

process_ip_file('ip_ports.txt')
