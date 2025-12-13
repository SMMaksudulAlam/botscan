import json

# File names
json_file = 'mapped_probes.json'
keys_file = 'key2del.txt'

# Step 1: Load the JSON data from mapped_probes.json
with open(json_file, 'r') as f:
    mapped_probes = json.load(f)

# Step 2: Read the keys from key2del.txt, one key per line
with open(keys_file, 'r') as f:
    keys_to_delete = [line.strip() for line in f.readlines()]

# Step 3: Delete the keys from the JSON data
for key in keys_to_delete:
    if key in mapped_probes:
        del mapped_probes[key]

# Step 4: Save the modified JSON data back to mapped_probes.json
with open(json_file, 'w') as f:
    json.dump(mapped_probes, f, indent=4)

print(f"Deleted keys from {json_file} and saved the updated file.")

