import pickle
file_name = 'first_probe.pkl'
with open(file_name, 'rb') as file:
    data = pickle.load(file)

print("Contents of the pickle file:")
res = []
dic = {}
print(len(data))
for sublist in data:
    if(len(sublist)>1):
    	res.append(sublist)
    else:
    	if(sublist and len(sublist[0])>12 and sublist[0][-8:] in ["2e656c66", "656c660a", "6c660d0a"]):
    		if(dic.get(sublist[0][:4])==None):
    			dic[sublist[0][:4]] = 1
    			res.append(sublist)
    		else:
    			pass
    	else:
    		res.append(sublist)
    			

print(len(res))
with open('first_probe.pkl', 'wb') as file:
    pickle.dump(res, file)

print(f"Data has been re-saved into {file_name}")

