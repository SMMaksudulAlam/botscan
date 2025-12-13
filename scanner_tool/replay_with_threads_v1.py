import socket
import threading
import time
import argparse
import json
import binascii
import pickle
import select

length = 16

class C2Replay:
    def __init__(self):
        self.data_received = []
        self.data_to_send = []
        self.isFirstProbeCompleted = False
        self.ip = ""
        self.port = 0
        self.s = None
        self.count = -1
        self.counts = []
        self.shouldStop = False
        self.socket_lock = threading.Lock()
        self.res_file = "res_file.txt"
        self.file_lock = threading.Lock()
        self.res_dic = {}
        #self.output_writer = None
        #self.output_lock = None
        self.data_sent = []
        
    def write_to_file(self, file_name, data):
        with self.file_lock:
            with open(file_name, 'a') as file:
                file.write(data + '\n')

    
    def reset_connection(self):
        self.counts.append(self.count)
        self.count = 0
        self.data_sent = []
        try:
            with self.socket_lock:
                if self.s:
                    self.s.close() 
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((self.ip, self.port)) 
            return self.s
        except Exception as e:
            self.shouldStop = True
            print(f"for {self.ip}:{self.port} connection reset got error!")
    """       
    def terminate(self, ioc):
    	self.shouldStop = True
    	self.write_to_file(self.res_file, f"{self.ip} {self.port} {ioc}")
    	self.count += 1
    	print(f"res got matched! for {self.ip}: {ioc}")
    """
    """	
    def output(self, ioc):
    	with self.output_lock:
    		self.output_writer.write(f"for {self.ip}:{self.port} data sent:\n")
    		for e in self.data_sent:
    			self.output_writer.write(f"{e} ")
    		self.output_writer.write(f"\n")
    		self.output_writer.write(f"{ioc}\n")
    """

    def receiver(self):
        global length
        print(f"for {self.ip}:{self.port} receiver started!")
        while True:
            if(self.shouldStop or any(val >=3 for val in self.res_dic.values()) or sum(self.res_dic.values())>=5):
                print(f"for {self.ip}:{self.port} getting out of receiver!")
                break
            try:
                try:
                    response = None
                    self.s.setblocking(False)
                    with self.socket_lock:
                        ready_to_read, _, _ = select.select([self.s], [], [], 0.005)
                        if ready_to_read:
                            response = self.s.recv(1024)
                except socket.error as e:
                    print(f"for {self.ip}:{self.port} in receiver, not proceeding further!")
                    time.sleep(0.5)
                    continue
                if(not response): 
                    time.sleep(0.1)
                    continue
                response = binascii.hexlify(response).decode('utf-8')
                if response != "":
                    self.isFirstProbeCompleted = True
                    self.data_received.append(response[:])
                    print(f"{self.ip} {self.port} received: {response}")
                    if "7f454c4601" in response:
                    	if "4261642072657175657374" not in response:
                    		#self.terminate(response)
                    		#self.output(f"{self.ip} {self.port} received matched {response}")
                    		self.write_to_file(self.res_file, f"{self.ip} {self.port} {response}")
                    		print((f"{self.ip} {self.port} received matched {response}"))
                    		self.count += 1
                    		break
                    if "212a20" in response or "5343414e4e4552204f4e0a" in response:
                    	if "4261642072657175657374" not in response:
                    		#self.terminate(response)
                    		#self.output(f"{self.ip} {self.port} received matched {response}")
                    		self.write_to_file(self.res_file, f"{self.ip} {self.port} {response}")
                    		print((f"{self.ip} {self.port} received matched {response}"))
                    		self.count += 1
                    		break
                    if "77676574202" in response:
                    	if "4261642072657175657374" not in response:
                    		#self.terminate(response)
                    		#self.output(f"{self.ip} {self.port} received matched {response}")
                    		self.write_to_file(self.res_file, f"{self.ip} {self.port} {response}")
                    		print((f"{self.ip} {self.port} received matched {response}"))
                    		self.count += 1
                    		break 
                    if "7075647020" in response or "6578656320" in response:
                    	if "4261642072657175657374" not in response:
                    		#self.terminate(response)
                    		#self.output(f"{self.ip} {self.port} received matched {response}")
                    		self.write_to_file(self.res_file, f"{self.ip} {self.port} {response}")
                    		print((f"{self.ip} {self.port} received matched {response}"))
                    		self.count += 1
                    		break
                    if "6775647020" in response or "63686d6f6420" in response or "202e2f" in response:
                    	if "4261642072657175657374" not in response:
                    		#self.terminate(response)
                    		#self.output(f"{self.ip} {self.port} received matched {response}")
                    		self.write_to_file(self.res_file, f"{self.ip} {self.port} {response}")
                    		print((f"{self.ip} {self.port} received matched {response}"))
                    		self.count += 1
                    		break
            except Exception as e:
                print(f"for {self.ip}:{self.port} An error occurred in receiver: {e}")

    def sender(self):
        print(f"for {self.ip}:{self.port} sender started!")
        while True:
            if(self.shouldStop or any(val >=3 for val in self.res_dic.values()) or sum(self.res_dic.values())>=5):
                print(f"for {self.ip}:{self.port} getting out of sender!")
                break
            try:
                time.sleep(1)
                try:
                    self.s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                except socket.error as e:
                    if e.errno == socket.EBADF:
                        print(f"for {self.ip}:{self.port} in sender, not proceeding further!")
                        continue
                if len(self.data_to_send) == 0:
                    continue
                else:
                    payload = self.data_to_send.pop(0)
                    with self.socket_lock:
                        self.s.sendall(payload)
                    #self.output(f"{self.ip} {self.port} sent {payload}")
                    self.data_sent.append(payload)
                    print(f"for {self.ip}:{self.port} sent: ", payload)

            except Exception as e:
                print(f"for {self.ip}:{self.port} An error occurred in sender: {e}")

    def generate_probes(self):
        print(f"for {self.ip}:{self.port} generate_probes started!")
        data = None
        with open("mapped_probes.json", "r") as file:
            data = json.load(file)

        first_probe = None
        with open('first_probe.pkl', 'rb') as file:
            first_probe = pickle.load(file)
        starting = True
        while True:
            if(self.shouldStop or any(val >=3 for val in self.res_dic.values()) or sum(self.res_dic.values())>=5):
                print(f"for {self.ip}:{self.port} getting out of generating probles!")
                break
            payloads = None
            if self.isFirstProbeCompleted:
                payloads = data

                if len(self.data_received) != 0:
                    key = self.data_received.pop(0)
                    print(f"for {self.ip}:{self.port} from mapping: ", key)
                    if (payloads.get(key) == None):
                        print(f"for {self.ip}:{self.port} probe got unmatched!: ", key)
                        self.data_to_send = []
                        self.data_received = []
                        self.s = self.reset_connection()


                        self.isFirstProbeCompleted = False
                        continue
                    else:
                        if(self.res_dic.get(key) == None):
                        	self.res_dic[key] = 0
                        self.res_dic[key] += 1
                        if(key[:12] != "5353482d322e"):
                        	self.count += 1
                        	print(f"for {self.ip}:{self.port} response matched!  {self.count}")
                        	self.write_to_file(self.res_file, f"{self.ip} {self.port} {key}")
                        	#self.output(f"{self.ip} {self.port} received matched {key}")
                        	print(f"{self.ip} {self.port} received matched {key}")
                        for k in payloads[key].keys():
                            payload = k
                            if payload != "":
                                self.data_to_send.append(bytes.fromhex(payload))
                                break
                            else:
                                time.sleep(1)


                else:
                    print(f"for {self.ip}:{self.port} no data recieved, so waiting!")
                    time.sleep(5)
                    if(len(self.data_received) == 0 and len(self.data_to_send) == 0):
                        self.data_to_send = []
                        self.data_received = []
                        self.s = self.reset_connection()
                        print(f"for {self.ip}:{self.port} connection got reset to send other first probes!", self.data_received, self.data_to_send)
                        self.isFirstProbeCompleted = False

            else:
                payloads = first_probe
                if starting:
                    starting = False
                else:
                    if(len(self.data_received)==0 and len(self.data_to_send) == 0):
                        print(f"for {self.ip}:{self.port} waiting to get response from server!")
                        time.sleep(5)
                        if(len(self.data_received)==0 and len(self.data_to_send) == 0):
                            print(f"for {self.ip}:{self.port} connection got reset to send other first probes!", self.data_received, self.data_to_send)
                            self.s = self.reset_connection()
                    else:
                        time.sleep(1)
                    

                if(len(first_probe)!=0):
                    probes = first_probe.pop(0)
                    if(len(probes) == 0):
                        print(f"for {self.ip}:{self.port} no probe is availabe!")
                        continue
                    for e in probes:
                        if(not self.isFirstProbeCompleted):
                            self.data_to_send.append(bytes.fromhex(e))
                            time.sleep(2)
                        else:
                            if(len(self.data_received)!=0):
                                self.isFirstProbeCompleted = True
                                print(f"for {self.ip}:{self.port} got response from the server!")
                            else:
                                print(f"for {self.ip}:{self.port} data_received got empty!")
                            break
                else:
                    self.shouldStop = True
                    print(f"for {self.ip}:{self.port} all first_probe ended!")

    def replay(self, _ip, _port):

        self.ip = _ip
        self.port = _port
        #self.output_writer = _output_writer
        #self.output_lock = _output_lock
        self.isFirstProbeCompleted = False
        self.s = self.reset_connection()
        print(f"for {self.ip}:{self.port} Connection established!")

        receiver_thread = threading.Thread(target=self.receiver)
        sender_thread = threading.Thread(target=self.sender)
        generate_probes_thread = threading.Thread(target=self.generate_probes)

        receiver_thread.start()
        time.sleep(5)
        generate_probes_thread.start()
        sender_thread.start()


        receiver_thread.join()
        generate_probes_thread.join()
        sender_thread.join()
        self.counts.append(self.count)
        with self.socket_lock:
            if(self.s != None):
                self.s.close()
        print(f"for {self.ip}:{self.port} returning from replaying!")
        return max(self.counts)
