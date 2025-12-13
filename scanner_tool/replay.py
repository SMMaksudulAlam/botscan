import scan_with_masscan
import replay_with_threads_v1
import argparse
import sys

class ReplayHandler:
    def __init__(self):
        pass

    def replay_ip(self, ip):
        ps = scan_with_masscan.PortScanner()
        open_ports = ps.scan_open_ports(ip)
        if(open_ports == None):
            return False, -1, None
        if len(open_ports) > 20:
            print(f" for {ip} more than 20 ports are open!")
            # sys.exit(1)
            return False, -2, None
        if len(open_ports) == 0:
            return False, -3, None
        print(f"for {ip} open ports: ", open_ports)

        max_count = 0
        max_port = None

        for port in open_ports:
            c2R = replay_with_threads_v1.C2Replay()
            count = c2R.replay(ip, port)
            print(f"for {ip}, got the count: {count}!")
            if count > 0:
                # sys.exit(1)
                if(count>max_count):
                    max_count = count
                    max_port = port
                break

        if(max_count>0):
        	if(max_count>1):
        		print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {ip} is a C2 Server! count of matched probes: {max_count}!")
        		"""with output_lock:
        			output_writer.write(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {ip} {port} is a C2 Server! count of matched probes: {max_count}!\n")"""
        	else:
        		print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {ip} is a likely C2 Server!")
        		"""with output_lock:
        			output_writer.write(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {ip} {port} is a likely C2 Server!\n")"""
        	return True, max_count, max_port

        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {ip} is not a C2 Server!")
        # sys.exit(0)
        return False, 0, None
