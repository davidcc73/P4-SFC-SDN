#!/usr/bin/env python2
from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import csv
import fcntl
import Queue
import sys
import os
import argparse
import threading
from scapy.all import sniff, get_if_hwaddr, TCP, UDP, IP
from io import open

# Global variables to store metrics per flow
flows_metrics = {}
flows_lock = threading.Lock()

# Define the directory path inside the container
result_directory = u"/INT/results"

args = None
packet_queue = Queue.Queue()
out_of_order_packets = []

def get_if_with_zero():
    # Find all interfaces from /sys/class/net/
    ifaces = [i for i in os.listdir(u'/sys/class/net/') if u'0' in i]
    
    # Filter interfaces that end with '0'
    iface = (i for i in ifaces if i[-1] == u'0'), None.next()
    
    if iface:
        return iface
    else:
        print "Cannot find any interface ending with '0'"
        exit(1)

def handle_pkt(pkt):
    packet_queue.put(pkt)

def process_packet(pkt):  # Process packets in queue
    global flows_metrics  # Dictionary to track metrics per flow
    flow_key = None
    
    if UDP in pkt:
        flow_key = (pkt[IP].src, pkt[IP].dst, pkt[UDP].sport, pkt[UDP].dport)
    elif TCP in pkt:
        flow_key = (pkt[IP].src, pkt[IP].dst, pkt[TCP].sport, pkt[TCP].dport)

    if flow_key is None:
        return  # Ignore non-TCP/UDP packets

    # Extract and process the payload
    payload = None
    if TCP in pkt and pkt[TCP].payload:
        payload = pkt[TCP].payload.load.decode(u'utf-8', u'ignore')
    elif UDP in pkt and pkt[UDP].payload:
        payload = pkt[UDP].payload.load.decode(u'utf-8', u'ignore')

    with flows_lock:  # Ensure only one thread modifies flows_metrics at a time
        # Initialize flow metrics if this is the first packet for this flow
        if flow_key not in flows_metrics:
            flows_metrics[flow_key] = {
                u"packet_count": 0,
                u"sequence_numbers": [],
                u"first_packet_time": pkt.time,
                u"DSCP": pkt[IP].tos >> 2,
                u"last_arrival_time": None,     # Track timestamp of the last packet arrival for jitter calculation
                u"avg_jitter": None             # Store the average jitter for the flow
            }


        try:
            seq_number, message = payload.split(u'-', 1)
            seq_number = int(seq_number)  # Ensure the sequence number is an integer
            flows_metrics[flow_key][u"sequence_numbers"].append(seq_number)
            print "Flow " + str(flow_key) + "- Packet Sequence Number: " + str(seq_number)
        except ValueError:
            print "Flow " + str(flow_key) + "- Error splitting payload: " + str(payload)

        
        #------------------Calculate Jitter------------------
        # Track the timestamp of the current packet arrival
        current_time = pkt.time
        if flows_metrics[flow_key][u"avg_jitter"] is None:
            flows_metrics[flow_key][u"avg_jitter"] = 0
        else:
            previous_pkt_count                    = flows_metrics[flow_key][u"packet_count"]
            current_jitter                        = current_time - flows_metrics[flow_key][u"last_arrival_time"]
            current_avg_jitter_undone             = flows_metrics[flow_key][u"avg_jitter"] * previous_pkt_count
            flows_metrics[flow_key][u"avg_jitter"] = (current_avg_jitter_undone + current_jitter) / (previous_pkt_count + 1)

        flows_metrics[flow_key][u"last_arrival_time"] = current_time

        # Increment the packet count for this flow
        flows_metrics[flow_key][u"packet_count"] += 1

    sys.stdout.flush()

def packet_processor():  # Thread that processes packets in queue
    while True:
        pkt = packet_queue.get()
        if pkt is None:
            break
        process_packet(pkt)
        packet_queue.task_done()

def terminate():
    print "Starting terminate"
    print "Flow Metrics Summary:"
    
    # Print metrics for each flow
    with flows_lock:
        for flow_key, metrics in flows_metrics.items():
            src_ip, dst_ip, sport, dport = flow_key
            packet_count = metrics[u"packet_count"]
            sequence_numbers = metrics[u"sequence_numbers"]
            out_of_order_count = len(set(xrange(1, max(sequence_numbers, default=1) + 1)) - set(sequence_numbers))

            print f"Flow {flow_key} - Total Packets: {packet_count}, Sequence Numbers: {sequence_numbers}, Out of Order Packets Count: {out_of_order_count}"

    export_results()

def export_results():
    print "Starting export_results()"
    global args
    os.makedirs(result_directory, exist_ok=True)

    # Define the filename
    filename_results = args.export
    lock_filename = f"LOCK_{filename_results}"
    
    # Combine the directory path and filename
    full_path_results = os.path.join(result_directory, filename_results)
    full_path_LOCK = os.path.join(result_directory, lock_filename)
    
    # Open the lock file
    with open(full_path_LOCK, u'w') as lock_file:
        try:
            # Acquire an exclusive lock on the lock file
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            
            # Check if the results file exists
            file_exists = os.path.exists(full_path_results)

            # Open the results file for appending
            print "Exporting results to" + full_path_results
            with open(full_path_results, mode=u'a', newline=u'') as file:
                # Create a CSV writer object
                writer = csv.writer(file)
                
                # If file does not exist, write the header row
                if not file_exists:
                    header = [u"Iteration", u"Host", u"IP Source", u"IP Destination", u"Source Port", u"Destination Port", u"Is", u"Number", u"Timestamp (seconds-Unix Epoch)", u"Nº pkt out of order", u"Out of order packets", u"DSCP", u"Avg Jitter (Nanoseconds)"]
                    writer.writerow(header)

                with flows_lock:  # Ensure only one thread modifies flows_metrics at a time
                    for flow_key, metrics in flows_metrics.items():
                        src_ip, dst_ip, sport, dport = flow_key
                        first_packet_time = metrics[u"first_packet_time"]
                        out_of_order_packets = sorted(set(xrange(1, max(metrics[u"sequence_numbers"], default=1) + 1)) - set(metrics[u"sequence_numbers"]))
                        jitter = metrics[u"avg_jitter"] * 1000000000

                        line = [args.iteration, args.me, src_ip, dst_ip, sport, dport, u"receiver", metrics[u"packet_count"], first_packet_time, len(out_of_order_packets), out_of_order_packets, metrics[u"DSCP"], jitter]
                        
                        # Write data
                        writer.writerow(line)
        
        finally:
            # Release the lock
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    print "Results exported"

def parse_args():
    global args
    parser = argparse.ArgumentParser(description=u'receiver parser')

    # Non-mandatory flag
    parser.add_argument(u'--export', help=u'File to export results', 
                        type=unicode, action=u'store', required=False, default=None)
    
    # Group of flags that are mandatory if --export is used
    parser.add_argument(u'--me', help=u'Name of the host running the script', 
                        type=unicode, action=u'store', required=False, default=None)
    parser.add_argument(u'--iteration', help=u'Current test iteration number', 
                        type=int, action=u'store', required=False, default=None)
    parser.add_argument(u'--duration', help=u'Current test duration seconds', 
                        type=float, action=u'store', required=False, default=None)
    
    args = parser.parse_args()
    if args.export is not None:
        if not args.me:
            parser.error(u'--me is required when --export is used')
        if not args.iteration:
            parser.error(u'--iteration is required when --export is used')

def main():
    global args
    parse_args()

    # Find interface ending in '0'
    iface = get_if_with_zero()
    
    # Capture only incoming IPv4 packets
    bpf_filter = u"ip and inbound"
    
    print "Starting sniffing for " + str(args.duration) + " seconds..."
    processor_thread = threading.Thread(target=packet_processor)
    processor_thread.start()
    sniff(
        iface=iface, 
        prn=handle_pkt, 
        filter=bpf_filter,
        timeout=args.duration        # set timeout, if not set, sniff will run indefinitely
    )
    
    packet_queue.put(None)
    processor_thread.join()

    # Call terminate explicitly after the timeout
    terminate()

if __name__ == u'__main__':
    main()
