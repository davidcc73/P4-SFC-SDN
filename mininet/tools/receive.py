#!/usr/bin/env python
import csv
import fcntl
import queue
import sys
import os
import argparse
import threading
from scapy.all import sniff, get_if_hwaddr, TCP, UDP


# Global variables to count packets and store sequence numbers
packet_TCP_UDP_count = 0
out_of_order_packets = []
sequence_numbers = []
results = {}

# Define the directory path inside the container
result_directory = "/INT/results"

args = None
packet_queue = queue.Queue()
#last_packet_time = None  # Initialize to keep track of the time of the last packet

def get_if_with_zero():
    # Find all interfaces from /sys/class/net/
    ifaces = [i for i in os.listdir('/sys/class/net/') if '0' in i]
    
    # Filter interfaces that end with '0'
    iface = next((i for i in ifaces if i[-1] == '0'), None)
    
    if iface:
        return iface
    else:
        print("Cannot find any interface ending with '0'")
        exit(1)

def handle_pkt(pkt):
    packet_queue.put(pkt)

def process_packet(pkt):            #process pkts in queue
    global packet_TCP_UDP_count, sequence_numbers, results #, last_packet_time
    packet_TCP_UDP_count += 1

    #print("got a TCP/UDP packet")

    print("Original packet received:")
    pkt.show2()
    sys.stdout.flush()
    
    '''
    #store flow info of the packet, and when was first packet received if not already stored
    if "flow" not in results:
        results["flow"] = (pkt[IP].src, pkt[IP].dst, pkt[IP].fl)
        results["first_packet_time"] = pkt.time
    

    #----------Extract and print the message from the packet
    if TCP in pkt and pkt[TCP].payload:
        payload = pkt[TCP].payload.load.decode('utf-8', 'ignore')
    elif UDP in pkt and pkt[UDP].payload:
        payload = pkt[UDP].payload.load.decode('utf-8', 'ignore')
    
    try:
        seq_number, message = payload.split('-', 1)
        seq_number = int(seq_number)  # Ensure the sequence number is an integer
        sequence_numbers.append(seq_number)
        print(f"Packet Sequence Number: {seq_number} Packet Message: {message}")
    except ValueError:
        print(f"Error splitting payload: {payload}")
    '''
    
    sys.stdout.flush()

def packet_processor():     #thread that processes pkts in queue
    while True:
        pkt = packet_queue.get()
        if pkt is None:
            break
        process_packet(pkt)
        packet_queue.task_done()


def terminate():
    print("Starting terminate")

    global sequence_numbers, packet_TCP_UDP_count, out_of_order_packets
    # Determine out-of-order packets by comparing each packet with the previous one
    last_seq_num = None
    print("All received:", sequence_numbers)
    for seq in sequence_numbers:
        if last_seq_num is not None and seq <= last_seq_num:
            out_of_order_packets.append(seq)
        last_seq_num = seq
    
    print("\nTotal TCP/UDP packets received:", packet_TCP_UDP_count)
    print("Out of order packets count:", len(out_of_order_packets))
    print("Out of order packets:", out_of_order_packets)

    export_results()
    print("Results exported")

def export_results():
    print("Exporting results")
    global args, results, packet_TCP_UDP_count
    
    os.makedirs(result_directory, exist_ok=True)

    # Define the filename
    filename_results = args.export
    lock_filename = f"LOCK_{filename_results}"
    
    # Combine the directory path and filename
    full_path_results = os.path.join(result_directory, filename_results)
    full_path_LOCK = os.path.join(result_directory, lock_filename)
    
    # Open the lock file
    with open(full_path_LOCK, 'w') as lock_file:
        try:
            # Acquire an exclusive lock on the lock file
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            
            # Check if the results file exists
            file_exists = os.path.exists(full_path_results)

            # Open the results file for appending
            print("Exporting results to", full_path_results)
            with open(full_path_results, mode='a', newline='') as file:
                # Create a CSV writer object
                writer = csv.writer(file)
                
                # If file does not exist, write the header row
                if not file_exists:
                    header = ["Iteration", "IP Source", "IP Destination", "Flow Label", "Is", "Number", "Timestamp (seconds-Unix Epoch)", "Nº pkt out of order", "Out of order packets"]
                    writer.writerow(header)

                #Prepare CSV line
                src_ip = results["flow"][0]
                dst_ip = results["flow"][1]
                flow_label = results["flow"][2]
                first_packet_time = results["first_packet_time"]
                line = [args.iteration, src_ip, dst_ip, flow_label, "receiver", packet_TCP_UDP_count, first_packet_time, len(out_of_order_packets), out_of_order_packets]

                # Write data
                writer.writerow(line)
        
        finally:
            # Release the lock
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    print("Results exported")

def parse_args():
    global args
    parser = argparse.ArgumentParser(description='receiver parser')

    # Non-mandatory flag
    parser.add_argument('--export', help='File to export results', 
                        type=str, action='store', required=False, default=None)
    
    # Group of flags that are mandatory if --export is used
    parser.add_argument('--me', help='Name of the host running the script', 
                        type=str, action='store', required=False, default=None)
    parser.add_argument('--iteration', help='Current test iteration number', 
                        type=int, action='store', required=False, default=None)
    parser.add_argument('--duration', help='Current test duration seconds', 
                        type=float, action='store', required=False, default=None)
    
    args = parser.parse_args()
    if args.export is not None:
        if not args.me:
            parser.error('--me is required when --export is used')
        if not args.iteration:
            parser.error('--iteration is required when --export is used')

def main():
    global args
    parse_args()

    # Find interface ending in '0'
    iface = get_if_with_zero()
    
    # Capture only incoming IPv4 packets
    bpf_filter = "ip and inbound"
    
    print(f"Starting sniffing for {args.duration} seconds...")
    processor_thread = threading.Thread(target=packet_processor)
    processor_thread.start()
    sniff(
        iface=iface, 
        prn=handle_pkt, 
        filter=bpf_filter,
        timeout = args.duration        # set timeout, if not set, sniff will run indefinitely
    )
    
    packet_queue.put(None)
    processor_thread.join()

    # Call terminate explicitly after the timeout
    #terminate()

if __name__ == '__main__':
    main()
