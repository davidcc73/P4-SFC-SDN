#!/usr/bin/env python
import argparse
from datetime import datetime
import sys
import socket
import random
import struct
import time  # Add time module for sleep
from scapy.all import sendp, get_if_list, get_if_hwaddr, get_if_addr
from scapy.all import Ether, IP, TCP, UDP

args = None

def get_if():
    ifs = get_if_list()
    iface = None
    for i in ifs:
        if "eth0" in i:
            iface = i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

# Check if the specified packet size is enough to include all the headers
def check_header_size():
    global args
    # Calculate the size of headers (Ethernet + IPv4 + TCP/UDP)
    if args.l4 == 'tcp':
        header_size = len(Ether() / IP() / TCP())
    elif args.l4 == 'udp':
        header_size = len(Ether() / IP() / UDP())

    # Check if the specified size is enough to include all the headers
    if args.s < header_size:
        print(f"Error: Specified size {args.s} bytes is not enough to include all the headers (at least {header_size} bytes needed).")
        sys.exit(1)

    return header_size

def send_packet(args, pkt_ETHE, payload_space, iface, addr, src_ip):

    global my_IP
    results = {
        'first_timestamp': None,
        'failed_packets': 0
    }

    #prev_timestamp = None
    l3_layer = IP(src=src_ip, dst=addr, tos=args.dscp << 2)

    # Construct l4 layer, TCP or UDP
    if args.l4 == 'tcp':
        l4_layer = TCP(sport=args.sport, dport=args.dport)
    elif args.l4 == 'udp':
        l4_layer = UDP(sport=args.sport, dport=args.dport)

    Base_pkt = pkt_ETHE / l3_layer / l4_layer 
    my_IP = Base_pkt[IP].src

    for i in range(args.c):
        # Reset packet
        pkt = Base_pkt

        # Adjust payload for each packet
        payload = f"{i + 1}-{args.m}".encode()  # Convert payload to bytes
        
        # Ensure payload length matches payload_space
        if len(payload) < payload_space:
            trash_data = b'\x00' * (payload_space - len(payload))
            payload += trash_data
        elif len(payload) > payload_space:
            payload = payload[:payload_space]

        pkt = pkt / payload

        # Set the timestamp of the first packet sent
        if results['first_timestamp'] is None:
            dt = datetime.now()
            ts = datetime.timestamp(dt)
            results['first_timestamp'] = ts             
        
        '''
        #----------------------Record the current timestamp
        current_timestamp = datetime.timestamp(datetime.now())

        # Print the interval if previous timestamp exists
        
        if prev_timestamp is not None:
            interval = current_timestamp - prev_timestamp
            print(f"Interval since last packet: {interval:.6f} seconds, thr expected: {args.i:.6f} seconds")
        '''

        pkt.show2()

        pre_timestamp = datetime.now()
        try:
            # Send the constructed packet
            sendp(pkt, iface=iface, inter=0, loop=0, verbose=True)
            #sendpfast(pkt, iface=iface, file_cache=True, pps=0, loop=0)
        except Exception as e:
            results['failed_packets'] += 1
            print(f"Packet {i + 1} failed to send: {e}")

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

def parse_args():
    global args
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description='sender parser')
    parser.add_argument('--c', help='number of probe packets',
                        type=int, action="store", required=False,
                        default=1)
    
    parser.add_argument('--dst_ip', help='dst ip',
                        type=str, action="store", required=True)
    
    parser.add_argument('--sport', help="src port", type=int,
                        action="store", required=True)
    
    parser.add_argument('--dport', help="dest port", type=int,
                        action="store", required=True)
    
    parser.add_argument('--l4', help="layer 4 proto (tcp or udp)",
                        type=str, action="store", required=True)
    
    parser.add_argument('--m', help="message", type=str,
                        action='store', required=False, default="")
    
    parser.add_argument('--dscp', help="DSCP value", type=int,
                        action='store', required=False, default=0)
    
    parser.add_argument('--i', help="interval to send packets (second)", type=float,
                        action='store', required=False, default=1.0)
        
    parser.add_argument('--s', help="packet's total size in bytes", type=int,
                        action='store', required=True)
    


    # Non-mandatory flag
    parser.add_argument('--export', help='File to export results', 
                        type=str, action='store', required=False, default=None)
    
    # Group of flags that are mandatory if --enable-feature is used
    parser.add_argument('--me', help='Name of the host running the script', 
                        type=str, action='store', required=False, default=None)
    parser.add_argument('--iteration', help='Current test iteration number', 
                        type=int, action='store', required=False, default=None)
    
    
    args = parser.parse_args()
    if args.export is not None:
        if not args.me:
            parser.error('--me is required when --export is used')
        if not args.iteration:
            parser.error('--iteration is required when --export is used')

def main():
    global args
    parse_args()

    addr = socket.gethostbyname(args.dst_ip)
    interval = args.i
    iface = get_if()
    src_ip = get_if_addr(iface)
    src_mac = get_if_hwaddr(iface)

    print("Sending packets on interface {} (IP: {}, MAC: {}) to {} every {} seconds".format(iface, src_ip, src_mac, addr, interval))
    
    dst_mac = '00:00:00:00:00:01'           #dummy value, currently no support for ARP and get the real MAC address of the destination
    pkt = Ether(src=src_mac, dst=dst_mac)

    header_size = check_header_size()

    payload_space = args.s - header_size

    results = send_packet(args, pkt, payload_space, iface, addr, src_ip)

    #if args.export is not None:
        # Export results
        #export_results(results)


if __name__ == '__main__':
    main()
