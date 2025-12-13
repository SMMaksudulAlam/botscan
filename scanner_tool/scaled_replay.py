import threading
import replay
import re
import os
import subprocess
import json
import time
from datetime import datetime


c2_file = None
likely_c2_file = None
too_many_ports_file = None
down_file = None
all_known_port_file = None
naive_file = None
explored_subnet = {}

def replay_single_ip(ip):
	global c2_file
	global likely_c2_file
	global too_many_ports_file
	global down_file
	global all_known_port_file
	global naive_file

	RH = replay.ReplayHandler()
	res, count, port = RH.replay_ip(ip)
	if(res == True):
		current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if(count>1):
			if(count>2):
				c2_file.write(f"{ip} {port}   {current_datetime}\n")
			else:
				c2_file.write(f"{ip} {port} 2   {current_datetime}\n")
		else:
			likely_c2_file.write(f"{ip} {port}   {current_datetime}\n")
	else:
		if(count == -1):
			down_file.write(f"{ip}\n")
		if(count == -2):
			too_many_ports_file.write(f"{ip}\n")
		if(count == -3):
			all_known_port_file.write(f"{ip}\n")
		if(count == 0):
			naive_file.write(f"{ip}\n")


def c2_file_open():
    global c2_file
    c2_file = open("c2.txt", "a")
	
def likely_c2_file_open():
    global likely_c2_file
    likely_c2_file = open("likely_c2.txt", "a")

def too_many_ports_file_open():
    global too_many_ports_file
    too_many_ports_file = open("too_many_ports.txt", "a")

def down_file_open():
    global down_file
    down_file = open("down.txt", "a")

def all_known_port_file_open():
    global all_known_port_file
    all_known_port_file = open("all_known_port.txt", "a")

def naive_file_open():
    global naive_file
    naive_file = open("naive.txt", "a")


def get_ips():
    with open("ips.txt", 'r') as file:
        ips = [line.strip() for line in file if line.strip()]
    return ips

"""
154.213.187 --> Mirai
117.209.86 --> Mozi
154.216.17 --> Gafgyt
45.200.149 --> Mirai
64.235.45 --> Mirai, single ip repeats
117.209.26 --> Mozi
154.216.18 --> Gafgyt
59.97.121 --> Mozi
178.215.238 --> Mirai
45.125.66 --> Mirai
117.209.22 --> Mozi
115.49.3 --> Mozi
117.235.108 --> Mozi
5.166.231 --> Hajime
223.151.72 --> Mozi
"""
ip_prefix_list = ['154.213.187', '117.209.86', '154.216.17', '45.200.149', '64.235.45' ,'117.209.26', '154.216.18', '59.97.121', '178.215.238', '45.125.66', '117.209.22', '115.49.3', '117.235.108', '5.166.231', '223.151.72']

while(True):
	for ip_prefix in ip_prefix_list:
		for i in range(0, 13):
		
			c2_file_open()
			likely_c2_file_open()
			too_many_ports_file_open()
			down_file_open()
			all_known_port_file_open()
			naive_file_open()
			
			f_ip_list = []
			s = i*20
			e = (i+1)*20
			for j in range(s, e):
				if(j>255):
					break
				f_ip_list.append(ip_prefix+"."+str(j))
			
			threads = []
			for ip in f_ip_list:
				print("............................................................................................" ,ip)
				thread = threading.Thread(target=replay_single_ip, args=(ip,))
				threads.append(thread)
				thread.start()

			for thread in threads:
			    thread.join()
		    
print("All replay threads have finished.")

