
import os
import time
from mininet.cli import CLI
from datetime import datetime, timezone

import constants

export_file_LOW = "LOW"
export_file_MEDIUM = "MEDIUM"
export_file_HIGH = "HIGH"
export_file_HIGH_EMERGENCY = "HIGH+EMERGENCY"

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

def SRv6_used(iteration_sleep, num_iter):
    print(f"ATTENTION: Running a test with SRv6, this requires that INT analyzer is also run at the same time")
    print(f"ATTENTION: The iteration sleep time for this test will be: {iteration_sleep} pass it to the INT analyzer script as argument")
    print(f"ATTENTION: The number of iterations for this test will be: {num_iter} pass it to the INT analyzer script as argument")
    print(f"ATTENTION: Press Enter to start the test, start the analyzer at the same time, they need to be in sync")
    input()

def print_menu():
    menu = """
    ONOS CLI Command Menu:
    ATTENTION: For clean results, delete the contents of the /INT/results directory before starting the tests
    0. Stop Mininet
    1. Mininet CLI
    2. Make all Hosts be detetced by ONOS (needed for packet forwarding)
    3. Low Load Test (Just for debugging, not the final test)
    4. Medium Load Test
    5. High Load Test
    6. High Load Test with Emergency Flow
    7. High -> High with Emergency Flow Tests in Sequence
    8. Medium -> High -> High with Emergency Flow Tests in Sequence
    """
    print(menu)

def print_routing_menu():
    menu = """
    Routing Method Menu:
    0. Cancel
    1. KShort
    2. ECMP
    3. ECMP + SRv6 (Do not use when selecting do the tests in sequence, analyzer may need different sleep times for each test)
    """

    while True:
        print(menu)
        try:
            print("Which Routing method is going to be used?")
            choice = int(input("Enter the number of your choice:"))
            if choice < 0 or choice > 3:
                print("Invalid choice. Please enter a valid number")
                continue

            return choice
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

def detect_all_hosts(net):
    #Iteratte all hosts, so their source switch send their info to ONOS, on how to forward to them
    print("Make all Hosts be detetced by ONOS")
    dst_host_ip = '2001:1:1::1'                                          #use as dst IP any host in the network
    for host in net.hosts:
        print(f"Detecting host {host.name}")
        command = f"nohup ping -c 3 -i 0.001 -w 0.001 "+dst_host_ip+" &"      #use as dst IP any host in the network
        host.cmd(command)

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
    dst_IP_and_maks = constants.host_IPs[dst_host.name]
    dst_IP = dst_IP_and_maks.split("/")[0]
    #print(f"dst_IP: {dst_IP}")

    num_packets = packet_number["Message"]
    timeout = receiver_timeout["Message"] 

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(src_host, dst_IP, l4, port, flow_label, msg, dscp, size, num_packets, i, file_results, iteration)

    #-------------Start the receive script on the destination hosts
    receive_packet_script(dst_host, file_results, iteration, timeout)

def create_Audio_flow(src_host, dst_host, flow_label, file_results, iteration):
    global intervals, packet_number, receiver_timeout
    i = intervals["Audio"]
    l4 = "udp"
    port = 443
    msg = "INTH1"
    dscp = 34
    size = 420                #Total byte size of the packet
    dst_IP_and_maks = constants.host_IPs[dst_host.name]
    dst_IP = dst_IP_and_maks.split("/")[0]
    #print(f"dst_IP: {dst_IP}")

    num_packets = packet_number["Audio"]
    timeout = receiver_timeout["Audio"]    

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(src_host, dst_IP, l4, port, flow_label, msg, dscp, size, num_packets, i, file_results, iteration)

    #-------------Start the receive script on the destination hosts
    receive_packet_script(dst_host, file_results, iteration, timeout)

def create_Video_flow(src_host, dst_host, flow_label, file_results, iteration):
    global intervals, packet_number, receiver_timeout
    i = intervals["Video"]
    l4 = "udp"
    port = 443
    msg = "INTH1"
    dscp = 35
    size = 874                #Total byte size of the packet
    dst_IP_and_maks = constants.host_IPs[dst_host.name]
    dst_IP = dst_IP_and_maks.split("/")[0]
    #print(f"dst_IP: {dst_IP}")

    num_packets = packet_number["Video"]
    timeout = receiver_timeout["Video"]     

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(src_host, dst_IP, l4, port, flow_label, msg, dscp, size, num_packets, i, file_results, iteration)

    #-------------Start the receive script on the destination hosts
    receive_packet_script(dst_host, file_results, iteration, timeout)

def create_Emergency_flow(src_host, dst_host, flow_label, file_results, iteration):
    global intervals, packet_number, receiver_timeout
    i = intervals["Emergency"]
    l4 = "udp"
    port = 443
    msg = "INTH1"
    dscp = 46
    size = 483                #Total byte size of the packet
    dst_IP_and_maks = constants.host_IPs[dst_host.name]
    dst_IP = dst_IP_and_maks.split("/")[0]
    #print(f"dst_IP: {dst_IP}")

    num_packets = packet_number["Emergency"]
    timeout = receiver_timeout["Emergency"]

    #-------------Start the send script on the source hosts (1º because it has a longer setup time)
    send_packet_script(src_host, dst_IP, l4, port, flow_label, msg, dscp, size, num_packets, i, file_results, iteration)

    #-------------Start the receive script on the destination hosts
    receive_packet_script(dst_host, file_results, iteration, timeout)

def low_load_test(net, routing):
    global export_file_LOW
    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(GREEN + "Low Load Test, started at:" + str(rfc3339_time) + END)

    file_results = export_file_LOW + "-" + routing + "_raw_results.csv"
    lock_filename = f"LOCK_{file_results}"

    #create logs directory
    os.makedirs("/INT/results/logs", exist_ok=True)
    create_lock_file(lock_filename)

    h1_1 = net.get("h1_1")
    h3_1 = net.get("h3_1")    
    
    num_iterations_LOW = 3        #for tests 3 is enough
    i = 0.001                     #seconds, lower values that 0.1, scapy sending/receiveing the pkt + sleep between emissions becomes inaccurate

    iteration_duration_seconds_LOW = 1 * 60                         #the duration of each iteration of the test
    num_packets = round(iteration_duration_seconds_LOW / (i + 0.1)) #distribute the packets over the duration of the test (over i intervals) and consider that each packet takes 0.1 sec to send/process at receive
    
    receiver_timeout = num_packets * 0.1 * 1.01         #each packet takes < 0.1 seconds to send/process at receive (may vary on the system), added small margin to ensure the receiver script receives all packets, before stopping
    iteration_sleep= receiver_timeout * 1.01            #with margin to ensure all receivers script have written the results with the concorrent writes prevention

    if routing == "ECMP-SRv6":
        SRv6_used(iteration_sleep, num_iterations_LOW)

    for iteration in range(1, num_iterations_LOW + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations_LOW}")
        
        #-------------Start the send script on the source hosts (1º longer setup time)
        send_packet_script(h1_1, "2001:1:3::1", "udp", 443, 1, "INTH1", 0, 262, num_packets, i, file_results, iteration)

        #-------------Start the receive script on the destination hosts
        receive_packet_script(h3_1, file_results, iteration, receiver_timeout)

        #-------------Keep the test running for a specified duration
        print(f"Waiting for {iteration_sleep} seconds")
        time.sleep(iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "Low Load Test finished at:" + str(rfc3339_time) + END)

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
    h1_1 = net.get("h1_1") 
    h1_2 = net.get("h1_2") 
    h2_1 = net.get("h2_1")
    h2_2 = net.get("h2_2")
    h3_1 = net.get("h3_1")
    h7_1 = net.get("h7_1")
    h8_1 = net.get("h8_1")
    h8_2 = net.get("h8_2")
    
    #See max sleep time between flows types to create
    max_iteration_sleep = max(iteration_sleep["Message"], iteration_sleep["Audio"], iteration_sleep["Video"])

    if routing == "ECMP-SRv6":
        SRv6_used(max_iteration_sleep, num_iterations)

    for iteration in range(1, num_iterations + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations}")
        
        #--------------Start Message flows
        create_Messages_flow(h8_1, h1_1, 1, file_results, iteration)
        create_Messages_flow(h2_1, h3_1, 1, file_results, iteration)

        #--------------Start Audio flows
        create_Audio_flow(h1_2, h7_1, 1, file_results, iteration)

        #--------------Start Video flows
        create_Video_flow(h2_2, h8_2, 1, file_results, iteration)

        #-------------Keep the test running for a specified duration
        print(f"Waiting for {max_iteration_sleep} seconds")
        time.sleep(max_iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "Medium Load Test finished at:" + str(rfc3339_time) + END)

def high_load_test(net, routing):
    global export_file_HIGH
    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(GREEN + "High Load Test, started at:" + str(rfc3339_time) + END)

    file_results = export_file_HIGH + "-" + routing + "_raw_results.csv"
    lock_filename = f"LOCK_{file_results}"

    #create logs directory
    os.makedirs("/INT/results/logs", exist_ok=True)
    create_lock_file(lock_filename)

    # Get the hosts
    h1_1 = net.get("h1_1") 
    h1_2 = net.get("h1_2") 
    h2_1 = net.get("h2_1")
    h2_2 = net.get("h2_2")
    h3_1 = net.get("h3_1")
    h5_1 = net.get("h5_1")
    h7_1 = net.get("h7_1")
    h7_2 = net.get("h7_2")
    h7_3 = net.get("h7_3")
    h8_1 = net.get("h8_1")
    h8_2 = net.get("h8_2")
    h8_3 = net.get("h8_3")
    h8_4 = net.get("h8_4")
    
    #See max sleep time between flows types to create
    max_iteration_sleep = max(iteration_sleep["Message"], iteration_sleep["Audio"], iteration_sleep["Video"])

    if routing == "ECMP-SRv6":
        SRv6_used(max_iteration_sleep, num_iterations)

    for iteration in range(1, num_iterations + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations}")
        
        #--------------Start Message flows
        create_Messages_flow(h8_1, h1_1, 1, file_results, iteration)
        create_Messages_flow(h2_1, h3_1, 1, file_results, iteration)

        #--------------Start Audio flows
        create_Audio_flow(h1_2, h7_1, 1, file_results, iteration)
        create_Audio_flow(h5_1, h7_2, 1, file_results, iteration)
        create_Audio_flow(h3_1, h5_1, 1, file_results, iteration)
        create_Audio_flow(h8_1, h2_1, 1, file_results, iteration)

        #--------------Start Video flows
        create_Video_flow(h2_2, h8_2, 1, file_results, iteration)
        create_Video_flow(h3_1, h8_3, 1, file_results, iteration)
        create_Video_flow(h3_1, h7_3, 1, file_results, iteration)
        create_Video_flow(h2_1, h8_1, 2, file_results, iteration)
        create_Video_flow(h7_3, h8_4, 1, file_results, iteration)
        create_Video_flow(h5_1, h2_2, 1, file_results, iteration)


        #-------------Keep the test running for a specified duration
        print(f"Waiting for {max_iteration_sleep} seconds")
        time.sleep(max_iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "High Load Test finished at:" + str(rfc3339_time) + END)

def high_emergency_load_test(net, routing):
    global export_file_HIGH_EMERGENCY
    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(GREEN + "High with Emergency Load Test, started at:" + str(rfc3339_time) + END)

    file_results = export_file_HIGH_EMERGENCY + "-" + routing + "_raw_results.csv"
    lock_filename = f"LOCK_{file_results}"

    #create logs directory
    os.makedirs("/INT/results/logs", exist_ok=True)
    create_lock_file(lock_filename)

    # Get the hosts
    h1_1 = net.get("h1_1") 
    h1_2 = net.get("h1_2") 
    h2_1 = net.get("h2_1")
    h2_2 = net.get("h2_2")
    h3_1 = net.get("h3_1")
    h5_1 = net.get("h5_1")
    h7_1 = net.get("h7_1")
    h7_2 = net.get("h7_2")
    h7_3 = net.get("h7_3")
    h8_1 = net.get("h8_1")
    h8_2 = net.get("h8_2")
    h8_3 = net.get("h8_3")
    h8_4 = net.get("h8_4")
    
    #See max sleep time between flows types to create
    max_iteration_sleep = max(iteration_sleep["Message"], iteration_sleep["Audio"], iteration_sleep["Video"], iteration_sleep["Emergency"])
    
    if routing == "ECMP-SRv6":
        SRv6_used(max_iteration_sleep, num_iterations)

    for iteration in range(1, num_iterations + 1):
        print(f"--------------Starting iteration {iteration} of {num_iterations}")

        #--------------Start Message flows
        create_Messages_flow(h8_1, h1_1, 1, file_results, iteration)
        create_Messages_flow(h2_1, h3_1, 1, file_results, iteration)

        #--------------Start Audio flows
        create_Audio_flow(h1_2, h7_1, 1, file_results, iteration)
        create_Audio_flow(h5_1, h7_2, 1, file_results, iteration)
        create_Audio_flow(h3_1, h5_1, 1, file_results, iteration)
        create_Audio_flow(h8_1, h2_1, 1, file_results, iteration)

        #--------------Start Video flows
        create_Video_flow(h2_2, h8_2, 1, file_results, iteration)
        create_Video_flow(h3_1, h8_3, 1, file_results, iteration)
        create_Video_flow(h3_1, h7_3, 1, file_results, iteration)
        create_Video_flow(h2_1, h8_1, 2, file_results, iteration)
        create_Video_flow(h7_3, h8_4, 1, file_results, iteration)
        create_Video_flow(h5_1, h2_2, 1, file_results, iteration)

        #--------------Start Emergency flows
        create_Emergency_flow(h8_4, h1_2, 1, file_results, iteration)


        #-------------Keep the test running for a specified duration
        print(f"Waiting for {max_iteration_sleep} seconds")
        time.sleep(max_iteration_sleep)  

    # Get the current time in FORMAT RFC3339
    rfc3339_time = datetime.now(timezone.utc).isoformat()
    print("---------------------------")
    print(CYAN + "High with Emergency Load Test finished at:" + str(rfc3339_time) + END)


def main_menu(net, choice):
    routing = None
    
    update_times()

    # Which routing method is going to be used?
    if choice == 3 or choice == 4 or choice == 5 or choice == 6 or choice == 7 or choice == 8:
        choise2 = print_routing_menu()
        if choise2 == 0:
            return True
        elif choise2 == 1:
            routing = "KShort"
        elif choise2 == 2:
            routing = "ECMP"
        elif choise2 == 3:
            routing = "ECMP-SRv6"


    # What will be done
    if   choice == 0:
        print("Stopping Mininet")
        net.stop()
        return False
    elif choice == 1:
        print("To leave the Mininet CLI, type 'exit' or 'quit'")
        CLI(net)
    elif choice == 2:
        detect_all_hosts(net)
    elif choice == 3:
        low_load_test(net, routing)                  #FOR LAST ONE, REMENBER TO CLEAN SRV6 BETWEEN TEST CASES
    elif choice == 4:
        medium_load_test(net, routing)
    elif choice == 5:
        high_load_test(net, routing)
    elif choice == 6:
        high_emergency_load_test(net, routing)
    elif choice == 7:
        high_load_test(net, routing)
        print(ORANGE + "Waiting for 10 seconds between tests scenarios" + END)
        time.sleep(15)
        
        high_emergency_load_test(net, routing)
    elif choice == 8:
        medium_load_test(net, routing)
        print(ORANGE + "Waiting for 10 seconds between tests scenarios" + END)
        time.sleep(15)

        high_load_test(net, routing)
        print(ORANGE + "Waiting for 10 seconds between tests scenarios" + END)
        time.sleep(15)
        
        high_emergency_load_test(net, routing)
    else:
        print("Invalid choice")
    
    return True