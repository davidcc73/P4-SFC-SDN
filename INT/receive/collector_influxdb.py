#!/usr/bin/env python3

import sys
import os
import json
import threading
from scapy.all import sniff
from influxdb import InfluxDBClient
from colllector import *

stop_sniffing = False

INFLUX_HOST = 'localhost'
INFLUX_DB = 'int'

# Dynamically determine the directory of the script and construct the file path
script_dir = os.path.dirname(os.path.realpath(__file__))
filename_with_sizes = os.path.join(script_dir, "packet sizes.json")

#global variable to store packet sizes of each DSCP value (to simplefy we associate each DSCP with a packet size, bytes)
packet_sizes = {}                       

#We work with reports that have this structure: 
#[Eth][IPv6][UDP][INT REPORT HDR][ETH][IPv6 (SRv6, Optional)][IPv6][UDP/TCP][INT HDR][INT DATA]


def read_json(file_path):
    """
    Reads a JSON file and returns its content as a dictionary.
    
    :param file_path: Path to the JSON file.
    :return: Dictionary containing the JSON data.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def handle_pkt(pkt,c):   #individually triggered by each sniffed packet
    print("got a TCP/UDP packet")
    pkt.show2()         #for debugging
    if INTREP in pkt :
        print("\n\n********* Receiving Telemetry Report ********")
        flow_info = c.parser_int_pkt(pkt, packet_sizes)
        flow_info.show()
        c.export_influxdb(flow_info)
    else:
        print("Packet does not contain INT report header")

def sniff_interface(iface, c):
    print("Sniffing on interface:", iface)
    sniff(iface = iface,filter='inbound and tcp or udp', prn = lambda x: handle_pkt(x, c), stop_filter=lambda _: stop_sniffing)

def main():
    try:
        influx_client = InfluxDBClient(host=INFLUX_HOST, database=INFLUX_DB)
        influx_client.ping()  # Check if connection is successful
        print("Connected to InfluxDB successfully.")
    except Exception as e:
        print("Failed to connect to InfluxDB:", e)
        sys.exit(1)  # Terminate the script with a non-zero exit code

    global packet_sizes
    packet_sizes = read_json(filename_with_sizes)
    print("Packet Sizes read:\n",packet_sizes)

    c = Collector(influx_client)
    print(influx_client)

    global stop_sniffing
    ifaces = [i for i in os.listdir('/sys/class/net/') if i.endswith('100')]

    if ifaces:
        print("Sniffing on interfaces:", ifaces)
        threads = []
        try:
            for iface in ifaces:
                sys.stdout.flush()
                t = threading.Thread(target=sniff_interface, args=(iface, c))
                threads.append(t)
                t.start()

            # Wait for all threads to finish
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            stop_sniffing = True
            print("\nCtrl+C detected. Terminating...")
            sys.exit(0)
    else:
        print("No interfaces ending with '100' found.")




if __name__ == '__main__':
    main()
