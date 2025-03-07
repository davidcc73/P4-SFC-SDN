
import os
import random
import time
from mininet.cli import CLI
from datetime import datetime, timezone

ORANGE = '\033[38;5;214m'
RED = '\033[31m'
BLUE = '\033[34m'
CYAN = '\033[36m'
GREEN = '\033[32m'
MAGENTA = '\033[35m'
PINK = '\033[38;5;205m'
END = "\033[0m"

export_file_HIGH = "HIGH"
export_file_HIGH_EMERGENCY = "HIGH+EMERGENCY"

host_IPs  = {"h1": "10.0.1.1/24", "h2": "10.0.2.2/24", "h3": "10.0.5.1/24", "h4": "10.0.1.2/24"}
intervals = {"Message": 0.1, "Audio": 0.1, "Video": 0.001, "Emergency": 0.001}       #seconds, used to update the other dictionaries
sizes     = {"Message": 262, "Audio": 420, "Video": 874, "Emergency": 483}           #bytes

packet_number    = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}            #placeholder values, updated in update_times()
receiver_timeout = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}            #placeholder values, updated in update_times(), time receiver will wait for pkts
iteration_sleep  = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}            #placeholder values, updated in update_times(), time between iterations

num_iterations = 10
iteration_duration_seconds = 5 * 60  #5 minutes, the duration of each iteration of the test
sender_receiver_gap = 1              #seconds to wait for the receiver to start before starting the sender

def update_times():
    global iteration_duration_seconds
    global intervals, packet_number, receiver_timeout, iteration_sleep

    #update the number of packets to be sent in each flow type
    packet_number["Message"]   = round(iteration_duration_seconds / (intervals["Message"]   + 0.1))
    packet_number["Audio"]     = round(iteration_duration_seconds / (intervals["Audio"]     + 0.1))
    packet_number["Video"]     = round(iteration_duration_seconds / (intervals["Video"]     + 0.1))
    packet_number["Emergency"] = round(iteration_duration_seconds / (intervals["Emergency"] + 0.1))

    receiver_timeout["Message"]   = packet_number["Message"]   * intervals["Message"]   * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout["Audio"]     = packet_number["Audio"]     * intervals["Audio"]     * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout["Video"]     = packet_number["Video"]     * intervals["Video"]     * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout["Emergency"] = packet_number["Emergency"] * intervals["Emergency"] * 1.05  + sender_receiver_gap * 1.05

    iteration_sleep["Message"]   = receiver_timeout["Message"]   * 1.05
    iteration_sleep["Audio"]     = receiver_timeout["Audio"]     * 1.05
    iteration_sleep["Video"]     = receiver_timeout["Video"]     * 1.05
    iteration_sleep["Emergency"] = receiver_timeout["Emergency"] * 1.05

def create_lock_file(lock_filename):
    lock_file_path = os.path.join("/INT/results", lock_filename)

    # Create the lock file if it does not exist
    if not os.path.exists(lock_file_path):
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write('') # Write an empty string to the file

def send_packet_script(me, dst_ip, l4, sport, dport, msg, dscp, size, count, interval, export_file, iteration):
    
    command = f"python3 /mininet/tools/send.py --dst_ip {dst_ip} --dscp {dscp} --l4 {l4} --sport {sport} --dport {dport} --m {msg} --s {size} --c {count} --i {interval}"
    
    if export_file != None:
        command = command + f" --export {export_file} --me {me.name} --iteration {iteration}"

    command = command + f" >> /INT/results/logs/send-{iteration}-{me.name}.log"
    command = command + " &"
    #print(f"{me.name} running Command: {command}")
    
    me.cmd(command)

def receive_packet_script(me, export_file, iteration, duration):
    command = f"python3 /mininet/tools/receive.py"

    if export_file != None:
        command = command + f" --export {export_file} --me {me.name} --iteration {iteration} --duration {duration}"

    command = command + f" >> /INT/results/logs/receive-{iteration}-{me.name}.log"
    command = command + " &"
    #print(f"{me.name} running Command: {command}")

    me.cmd(command)

def create_Messages_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = "udp"
    msg = "INTH1"
    i = intervals["Message"]
    size = sizes["Message"]                #Total byte size of the packet

    num_packets = packet_number["Message"]

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(me = src_host, dst_ip = dst_IP, l4 = l4, 
                        sport= sport, dport = dport, msg = msg, 
                        dscp = dscp, size = size, count = num_packets, 
                        interval = i, export_file = file_results, iteration = iteration)

def create_Audio_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = "udp"
    msg = "INTH1"
    i = intervals["Audio"]
    size = sizes["Audio"]                #Total byte size of the packet

    num_packets = packet_number["Audio"]

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(me = src_host, dst_ip = dst_IP, l4 = l4, 
                        sport= sport, dport = dport, msg = msg, 
                        dscp = dscp, size = size, count = num_packets, 
                        interval = i, export_file = file_results, iteration = iteration)

def create_Video_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = "udp"
    msg = "INTH1"
    i = intervals["Video"]
    size = sizes["Video"]                #Total byte size of the packet

    num_packets = packet_number["Video"]

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(me = src_host, dst_ip = dst_IP, l4 = l4, 
                        sport= sport, dport = dport, msg = msg, 
                        dscp = dscp, size = size, count = num_packets, 
                        interval = i, export_file = file_results, iteration = iteration)

def create_Emergency_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = "udp"
    msg = "INTH1"
    i = intervals["Emergency"]
    size = sizes["Emergency"]                #Total byte size of the packet

    num_packets = packet_number["Emergency"]

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(me = src_host, dst_ip = dst_IP, l4 = l4, 
                        sport= sport, dport = dport, msg = msg, 
                        dscp = dscp, size = size, count = num_packets, 
                        interval = i, export_file = file_results, iteration = iteration)
    
def high_load_test(net, routing):
    global export_file_HIGH
    dport = 443

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(GREEN + "High Load Test, started at:" + str(rfc3339_time) + END)

    file_results = export_file_HIGH + "-" + routing + "_raw_results.csv"
    lock_filename = f"LOCK_{file_results}"

    #create logs directory
    os.makedirs("/INT/results/logs", exist_ok=True)
    create_lock_file(lock_filename)

    #delete old .csv file if it exists
    if os.path.exists(f"/INT/results/{file_results}"):
        print(f"Deleting the old results file: {file_results}")
        os.remove(f"/INT/results/{file_results}")

    # Get the hosts
    h1 = net.get("h1") 
    h2 = net.get("h2") 
    h3 = net.get("h3") 
    h4 = net.get("h4") 
    
    # Get the hosts IPs
    h1_IP_and_maks = host_IPs[h1.name]
    h2_IP_and_maks = host_IPs[h2.name]
    h3_IP_and_maks = host_IPs[h3.name]
    h4_IP_and_maks = host_IPs[h4.name]
    h1_dst_IP = h1_IP_and_maks.split("/")[0]
    h2_dst_IP = h2_IP_and_maks.split("/")[0]
    h3_dst_IP = h3_IP_and_maks.split("/")[0]
    h4_dst_IP = h4_IP_and_maks.split("/")[0]


    #See max sleep time for receiver to wait for packets
    max_receiver_timeout = max(receiver_timeout["Message"], receiver_timeout["Audio"], receiver_timeout["Video"], receiver_timeout["Emergency"])
    #See max sleep time between flows types to create
    max_iteration_sleep = max(iteration_sleep["Message"], iteration_sleep["Audio"], iteration_sleep["Video"], iteration_sleep["Emergency"])

    #generate 5 different random sports between 49152 and 65535
    sports = random.sample(range(49152, 65535), 5)
    print(f"Sports: {sports}")

    for iteration in range(1, num_iterations + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations}")

        #-------------Start the receive script on the destination hosts
        receive_packet_script(h1, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h2, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h3, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h4, file_results, iteration, max_receiver_timeout)

        time.sleep(sender_receiver_gap) 
        
        #--------------Start Message flows
        create_Messages_flow (h1, h3_dst_IP, 0,  sports[0], dport, file_results, iteration)    #DSCP 0   
        create_Messages_flow (h1, h2_dst_IP, 0,  sports[1], dport, file_results, iteration)    #DSCP 0        
        create_Audio_flow    (h4, h2_dst_IP, 10, sports[2], dport, file_results, iteration)    #DSCP 10
        create_Video_flow    (h3, h4_dst_IP, 2,  sports[3], dport, file_results, iteration)    #DSCP 2
        create_Emergency_flow(h2, h1_dst_IP, 51, sports[4], dport, file_results, iteration)    #DSCP 51

        #-------------Keep the test running for a specified duration
        print(f"Waiting for {max_iteration_sleep} seconds")
        time.sleep(max_iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "High Load Test finished at:" + str(rfc3339_time) + END)

def print_menu():
    menu = """
    ONOS CLI Command Menu:
    ATTENTION: For clean results, delete the contents of the /INT/results directory before starting the tests
    0. Stop Mininet
    1. Mininet CLI
    2. High Load Test
    """
    print(menu)

def main_menu(net, choice):
    routing = None
    
    update_times()

    # What will be done
    if choice == 0:
        print("Stopping Mininet")
        net.stop()
        return False
    elif choice == 1:
        print("To leave the Mininet CLI, type 'exit' or 'quit'")
        CLI(net)
    elif choice == 2:
        print("Is SFC enabled? input number to choose\
                \n 1- Yes \
                \n 2- No")
        choice2 = input()
        if choice2 == "1":
            routing = "SFC"
        elif choice2 == "2":
            routing = "NO,SFC"
        else:
            print("Invalid choice")
            return True
        high_load_test(net, routing)
    else:
        print("Invalid choice")
    
    return True