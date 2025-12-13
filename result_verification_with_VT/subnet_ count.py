def count_unique_subnets(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        
    subnets = set()
    for line in lines:
        ip = line.strip()
        subnet = '.'.join(ip.split('.')[:3])
        subnets.add(subnet)
    
    unique_subnet_count = len(subnets)
    print(f'The number of unique /24 subnets is: {unique_subnet_count}')
count_unique_subnets('ips.txt')
