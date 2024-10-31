#!/usr/bin/python3


import argparse
import importlib
import json
import os
import interface

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo
from mininet.link import TCLink

from stratum import StratumBmv2Switch

CPU_PORT = 255

class DynamicTopo(Topo):


    def __init__(self, topology_config):
        Topo.__init__(self)

        # Create switches from the JSON config
        for switch_id, switch_info in topology_config['switches'].items():
            mac = switch_info["mac"]

            switch = self.addSwitch(switch_id, 
                                    cls=StratumBmv2Switch, 
                                    cpuport = CPU_PORT, 
                                    mac = mac, 
                                    loglevel="info") #, loglevel="info"


        # Create hosts
        for host_id, host_info in topology_config['hosts'].items():
            IP_GW = host_info["IP_GW"]
            MAC_GW = host_info["MAC_GW"]
        
            # Add hosts
            host = self.addHost(host_id, mac=host_info['mac'], ip=host_info['ip'], ip_gw = IP_GW)
        
        
        # Add links current host-switch, possible  combinations ["h1", "s1-p1" ], ["s1-p2", "s2-p1"]
        for link in topology_config['links']:
            element0 = link[0]
            element1 = link[1]

            #if both are switches
            if element0.startswith("s") and element1.startswith("s"):
                id_switch0 = element0.split("-")[0]
                id_switch1 = element1.split("-")[0]

                port_switch0 = int(link[0].split("p")[1])
                port_switch1 = int(link[1].split("p")[1])

                
                self.addLink(id_switch0, id_switch1, cls=TCLink, port1 = port_switch0, port2 = port_switch1)
                
            else:
                if element0.startswith("h"):
                    host = element0
                    switch = element1
                elif element1.startswith("h"):
                    host = element1
                    switch = element0
                
                id_switch = switch.split("-")[0]
                port_switch = int(switch.split("p")[1])

                id_host = host

                self.addLink(id_host, id_switch, port1 = 0, port2 = port_switch, cls=TCLink)



def main(args):
    # Load the all topology info from the JSON file
    with open(args.topology) as f:
        topology_config = json.load(f)

    
    topo = DynamicTopo(topology_config)
    controller = RemoteController('c0', ip="127.0.0.1")

    net = Mininet(topo=topo, controller=None)
    net.addController(controller)
    net.start()


    while True:
        try:
            importlib.reload(interface)  # TO MAKE DEGUG EASIER: Reload the module to reflect any changes, after any choice
            interface.print_menu()
            choice = int(input("Enter the number of your choice:"))
            result = interface.main_menu(net, choice)
            if not result:          
                break

        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

    net.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Topology Information')
    parser.add_argument('--topology', help='JSON file containing the topology configuration, for mininet dinamically \
                        create the topology, it must match netcfg.json',
                        type=str, action="store", required=False,
                        default='/config/topology.json')
    args = parser.parse_args()

    if not os.path.exists(args.topology):
        print("\nTopology JSON file not found: " + args.topology)
        parser.exit(1)


    main(args)
