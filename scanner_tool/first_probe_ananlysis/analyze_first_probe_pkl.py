import pickle


text_file_path = 'first_probes_parts.txt'

first_probe = None
with open('first_probe.pkl', 'rb') as file:
    first_probe = pickle.load(file)
    
    
    
with open(text_file_path, 'w') as text_file:
	print(f"total first probe count: {len(first_probe)}")
	for e in first_probe:
		while(e):
			key = e.pop(0)
			text_file.write(f"{key}\n")

print(f"first probes have been written to {text_file_path}")
