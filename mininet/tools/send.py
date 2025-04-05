#!/usr/bin/env python2
from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import argparse
import csv
from datetime import datetime
import fcntl
import os
import sys
import socket
import random
import struct
import time  # Add time module for sleep
from scapy.all import sendp, get_if_list, get_if_hwaddr, get_if_addr
from scapy.all import Ether, IP, TCP, UDP
from io import open

args = None

# Define the directory path inside the container
result_directory = u"/INT/results"

def get_if():
    ifs = get_if_list()
    iface = None
    for i in ifs:
        if u"eth0" in i:
            iface = i
            break
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

# Check if the specified packet size is enough to include all the headers
def check_header_size():
    global args
    # Calculate the size of headers (Ethernet + IPv4 + TCP/UDP)
    if args.l4 == u'tcp':
        header_size = len(Ether() / IP() / TCP())
    elif args.l4 == u'udp':
        header_size = len(Ether() / IP() / UDP())

    # Check if the specified size is enough to include all the headers
    if args.s < header_size:
        print "Error: Specified size {0} bytes is not enough to include all the headers (at least {1} bytes needed).".format(args.s, header_size)
        sys.exit(1)

    return header_size

def send_packet(args, pkt_ETHE, payload_space, iface, addr, src_ip):

    global my_IP
    results = {
        u'first_timestamp': None,
        u'failed_packets': 0
    }

    #prev_timestamp = None
    l3_layer = IP(src=src_ip, dst=addr, tos=args.dscp << 2)

    # Construct l4 layer, TCP or UDP
    if args.l4 == u'tcp':
        l4_layer = TCP(sport=args.sport, dport=args.dport)
    elif args.l4 == u'udp':
        l4_layer = UDP(sport=args.sport, dport=args.dport)

    Base_pkt = pkt_ETHE / l3_layer / l4_layer 
    my_IP = Base_pkt[IP].src

    for i in xrange(args.c):
        # Reset packet
        pkt = Base_pkt

        # Adjust payload for each packet
        payload = f"{i + 1}-{args.m}".encode()  # Convert payload to bytes
        
        # Ensure payload length matches payload_space
        if len(payload) < payload_space:
            trash_data = '\x00' * (payload_space - len(payload))
            payload += trash_data
        elif len(payload) > payload_space:
            payload = payload[:payload_space]

        pkt = pkt / payload

        # Set the timestamp of the first packet sent
        if results[u'first_timestamp'] is None:
            dt = datetime.now()
            ts = datetime.timestamp(dt)
            results[u'first_timestamp'] = ts             
        
        u'''
        #----------------------Record the current timestamp
        current_timestamp = datetime.timestamp(datetime.now())

        # Print the interval if previous timestamp exists
        
        if prev_timestamp is not None:
            interval = current_timestamp - prev_timestamp
            print(f"Interval since last packet: {interval:.6f} seconds, thr expected: {args.i:.6f} seconds")
        '''

        #pkt.show2()

        pre_timestamp = datetime.now()
        try:
            # Send the constructed packet
            sendp(pkt, iface=iface, inter=0, loop=0, verbose=False)
            #sendpfast(pkt, iface=iface, file_cache=True, pps=0, loop=0)
            print "({0}, {1}, {2}, {3}) Packet {4} sent".format(src_ip, args.dst_ip, args.sport, args.dport, i + 1)
        except Exception as e:
            results[u'failed_packets'] += 1
            print "({0}, {1}, {2}, {3}) Packet {4} failed to send: {5}".format(src_ip, args.dst_ip, args.sport, args.dport, i + 1, e)


        pkt_sending_time = datetime.now() - pre_timestamp
        pkt_sending_time_seconds = pkt_sending_time.total_seconds()
        #print(f"Packet sent in {pkt_sending_time_seconds} seconds")
        
        # Update previous timestamp
        #prev_timestamp = current_timestamp
        
        # Sleep for specified interval - the time it took to send the packet, must be subtracted
        rounded_number = round(args.i - pkt_sending_time_seconds)
        t = max(rounded_number, 0)
        time.sleep(t)
    
    return results

def export_results(results):
    # Write in the CSV file a line with the following format: 
    global args, result_directory
    num_packets_successefuly_sent = args.c - results[u'failed_packets']

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
                
                # Prepare the data line
                timestamp_first_sent = results[u'first_timestamp']
                line = [args.iteration, args.me, my_IP, args.dst_ip, args.sport, args.dport, u"sender", num_packets_successefuly_sent, timestamp_first_sent, None, None, args.dscp, None]
                
                # Write data
                writer.writerow(line)
                
        finally:
            # Release the lock on the lock file
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def parse_args():
    global args
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description=u'sender parser')
    parser.add_argument(u'--c', help=u'number of probe packets',
                        type=int, action=u"store", required=False,
                        default=1)
    
    parser.add_argument(u'--dst_ip', help=u'dst ip',
                        type=unicode, action=u"store", required=True)
    
    parser.add_argument(u'--sport', help=u"src port", type=int,
                        action=u"store", required=True)
    
    parser.add_argument(u'--dport', help=u"dest port", type=int,
                        action=u"store", required=True)
    
    parser.add_argument(u'--l4', help=u"layer 4 proto (tcp or udp)",
                        type=unicode, action=u"store", required=True)
    
    parser.add_argument(u'--m', help=u"message", type=unicode,
                        action=u'store', required=False, default=u"")
    
    parser.add_argument(u'--dscp', help=u"DSCP value", type=int,
                        action=u'store', required=False, default=0)
    
    parser.add_argument(u'--i', help=u"interval to send packets (second)", type=float,
                        action=u'store', required=False, default=1.0)
        
    parser.add_argument(u'--s', help=u"packet's total size in bytes", type=int,
                        action=u'store', required=True)
    


    # Non-mandatory flag
    parser.add_argument(u'--export', help=u'File to export results', 
                        type=unicode, action=u'store', required=False, default=None)
    
    # Group of flags that are mandatory if --enable-feature is used
    parser.add_argument(u'--me', help=u'Name of the host running the script', 
                        type=unicode, action=u'store', required=False, default=None)
    parser.add_argument(u'--iteration', help=u'Current test iteration number', 
                        type=int, action=u'store', required=False, default=None)
    
    
    args = parser.parse_args()
    if args.export is not None:
        if not args.me:
            parser.error(u'--me is required when --export is used')
        if not args.iteration:
            parser.error(u'--iteration is required when --export is used')

def main():
    global args
    parse_args()

    addr = socket.gethostbyname(args.dst_ip)
    interval = args.i
    iface = get_if()
    src_ip = get_if_addr(iface)
    src_mac = get_if_hwaddr(iface)

    print u"Sending packets on interface {} (IP: {}, MAC: {}) to {} every {} seconds".format(iface, src_ip, src_mac, addr, interval)
    
    dst_mac = u'00:00:00:00:00:01'           #dummy value, currently no support for ARP and get the real MAC address of the destination
    pkt = Ether(src=src_mac, dst=dst_mac)

    header_size = check_header_size()

    payload_space = args.s - header_size

    results = send_packet(args, pkt, payload_space, iface, addr, src_ip)

    if args.export is not None:
        # Export results
        export_results(results)


if __name__ == u'__main__':
    main()
