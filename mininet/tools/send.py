#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct
import time  # Add time module for sleep
from scapy.all import sendp, get_if_list, get_if_hwaddr
from scapy.all import Ether, IP, TCP

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip_addr', type=str, help="The destination IP address to use")
    parser.add_argument('-dscp', type=int, default=0, help="The DSCP field in the IP header")
    parser.add_argument('-i', type=float, default=1.0, help="Interval between packets in seconds")  # New argument for interval
    args = parser.parse_args()

    addr = socket.gethostbyname(args.ip_addr)
    interval = args.i
    iface = get_if()

    print("Sending packets on interface {} to {} every {} seconds".format(iface, addr, interval))

    while True:
        pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
        pkt = pkt / IP(dst=addr, tos=args.dscp << 2) / TCP(dport=1234, sport=random.randint(49152, 65535))
        pkt.show2()
        sendp(pkt, iface=iface, verbose=True)
        time.sleep(interval)  # Pause for the specified interval

if __name__ == '__main__':
    main()
