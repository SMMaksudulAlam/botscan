import json


file_path = 'mapped_probes.json'
text_file_path = 'keys_output.txt'

with open(file_path, 'r') as file:
    data = json.load(file)
    
    
    
with open(text_file_path, 'w') as text_file:
    for key in data.keys():
        text_file.write(f"{key}\n")

print(f"Keys have been written to {text_file_path}")