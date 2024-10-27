#!/usr/bin/env python
import sys
import os
import argparse
from scapy.all import sniff, get_if_hwaddr

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
    print("got a packet")
    pkt.show2()
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--if2", help="host-eth (interface)", default=None)
    args = parser.parse_args()

    # Use the argument if provided, otherwise find interface ending in '0'
    iface = args.if2 if args.if2 else get_if_with_zero()
    
    # Get the MAC address of the chosen interface
    mac_addr = get_if_hwaddr(iface)
    
    # Filter out packets with the source MAC address matching the host's MAC address (i.e., sent packets)
    bpf_filter = f"not ether src {mac_addr}"

    print(f"Sniffing on {iface}, ignoring packets sent from {mac_addr}")
    sys.stdout.flush()
    
    sniff(iface=iface, prn=lambda x: handle_pkt(x), filter=bpf_filter)

if __name__ == '__main__':
    main()
