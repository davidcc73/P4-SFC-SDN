
import os
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

intervals ={"Message": 0.1, "Audio": 0.1, "Video": 0.001, "Emergency": 0.001}   #seconds, used to update the other dictionaries
packet_number = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}
receiver_timeout = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}
iteration_sleep = {"Message": 0, "Audio": 0, "Video": 0, "Emergency": 0}

#ECMP will is only configured on ONOS to have rules for Flow labels between 0-4, if not, the packet will not be routed
num_iterations = 10
iteration_duration_seconds = 5 * 60  #5 minutes, the duration of each iteration of the test

def update_times():
    global iteration_duration_seconds
    global intervals, packet_number, receiver_timeout, iteration_sleep

    #update the number of packets to be sent in each flow type
    packet_number["Message"] = round(iteration_duration_seconds / (intervals["Message"] + 0.1))
    packet_number["Audio"] = round(iteration_duration_seconds / (intervals["Audio"] + 0.1))
    packet_number["Video"] = round(iteration_duration_seconds / (intervals["Video"] + 0.1))
    packet_number["Emergency"] = round(iteration_duration_seconds / (intervals["Emergency"] + 0.1))

    receiver_timeout["Message"] = packet_number["Message"] * 0.1 * 1.01 
    receiver_timeout["Audio"] = packet_number["Audio"] * 0.1 * 1.01
    receiver_timeout["Video"] = packet_number["Video"] * 0.1 * 1.01
    receiver_timeout["Emergency"] = packet_number["Emergency"] * 0.1 * 1.01

    iteration_sleep["Message"] = receiver_timeout["Message"] * 1.01
    iteration_sleep["Audio"] = receiver_timeout["Audio"] * 1.01
    iteration_sleep["Video"] = receiver_timeout["Video"] * 1.01
    iteration_sleep["Emergency"] = receiver_timeout["Emergency"] * 1.01

def create_lock_file(lock_filename):
    lock_file_path = os.path.join("/INT/results", lock_filename)

    # Create the lock file if it does not exist
    if not os.path.exists(lock_file_path):
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write('') # Write an empty string to the file

def print_menu():
    menu = """
    ONOS CLI Command Menu:
    ATTENTION: For clean results, delete the contents of the /INT/results directory before starting the tests
    0. Stop Mininet
    1. Mininet CLI
    2. Medium Load Test
    """
    print(menu)

def send_packet_script(me, dst_ip, l4, port, flow_label, msg, dscp, size, count, interval, export_file, iteration):
    
    command = f"python3 /INT/send/send.py --ip {dst_ip} --l4 {l4} --port {port} --flow_label {flow_label} --m {msg} --dscp {dscp} --s {size} --c {count} --i {interval}"
    
    if export_file != None:
        command = command + f" --export {export_file} --me {me.name} --iteration {iteration}"

    command = command + f" > /INT/results/logs/send-{iteration}.log"
    command = command + " &"
    #print(f"{me.name} running Command: {command}")
    
    me.cmd(command)

def receive_packet_script(me, export_file, iteration, duration):
    command = f"python3 /INT/receive/receive.py"

    if export_file != None:
        command = command + f" --export {export_file} --me {me.name} --iteration {iteration} --duration {duration}"

    command = command + f" > /INT/results/logs/receive-{iteration}.log"
    command = command + " &"
    #print(f"{me.name} running Command: {command}")

    me.cmd(command)

def create_Messages_flow(src_host, dst_host, flow_label, file_results, iteration):
    global intervals, packet_number, receiver_timeout
    i = intervals["Message"]
    l4 = "udp"
    port = 443
    msg = "INTH1"
    dscp = 0
    size = 262                #Total byte size of the packet
    dst_IP_and_maks = 0#constants.host_IPs[dst_host.name]
    dst_IP = dst_IP_and_maks.split("/")[0]
    #print(f"dst_IP: {dst_IP}")

    num_packets = packet_number["Message"]
    timeout = receiver_timeout["Message"] 

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(src_host, dst_IP, l4, port, flow_label, msg, dscp, size, num_packets, i, file_results, iteration)

    #-------------Start the receive script on the destination hosts
    receive_packet_script(dst_host, file_results, iteration, timeout)

def medium_load_test(net, routing):
    global export_file_MEDIUM
    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(GREEN + "Medium Load Test, started at:" + str(rfc3339_time) + END)

    file_results = export_file_MEDIUM + "-" + routing + "_raw_results.csv"
    lock_filename = f"LOCK_{file_results}"

    #create logs directory
    os.makedirs("/INT/results/logs", exist_ok=True)
    create_lock_file(lock_filename)

    # Get the hosts
    h1 = net.get("h1_1") 
    h2 = net.get("h1_2") 
    
    #See max sleep time between flows types to create
    max_iteration_sleep = max(iteration_sleep["Message"], iteration_sleep["Audio"], iteration_sleep["Video"])


    for iteration in range(1, num_iterations + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations}")
        
        #--------------Start Message flows
        create_Messages_flow(h2, h1, 1, file_results, iteration)

        #-------------Keep the test running for a specified duration
        print(f"Waiting for {max_iteration_sleep} seconds")
        time.sleep(max_iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "Medium Load Test finished at:" + str(rfc3339_time) + END)

## TODO: ADAPT TO SFC Project
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
        medium_load_test(net, routing)
    else:
        print("Invalid choice")
    
    return True