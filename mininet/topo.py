#!/usr/bin/python2


from __future__ import with_statement
from __future__ import absolute_import
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
from io import open

CPU_PORT = 255

class DynamicTopo(Topo):


    def __init__(self, topology_config):
        Topo.__init__(self)

        # Create switches from the JSON config
        for switch_id, switch_info in topology_config[u'switches'].items():
            mac = switch_info[u"mac"]

            switch = self.addSwitch(switch_id, 
                                    cls=StratumBmv2Switch, 
                                    cpuport = CPU_PORT, 
                                    mac = mac, 
                                    loglevel=u"info") #, loglevel="info"


        # Create hosts
        for host_id, host_info in topology_config[u'hosts'].items():
            IP_GW = host_info[u"IP_GW"]
            MAC_GW = host_info[u"MAC_GW"]
        
            # Add hosts
            if IP_GW == u"Empty":
                host = self.addHost(host_id, mac=host_info[u'mac'], ip=host_info[u'ip'])
            else:
                host = self.addHost(host_id, mac=host_info[u'mac'], ip=host_info[u'ip'], ip_gw = IP_GW)
        
        
        # Add links current host-switch, possible  combinations ["h1", "s1-p1" ], ["s1-p2", "s2-p1"]
        for link in topology_config[u'links']:
            element0 = link[0]
            element1 = link[1]

            #if both are switches
            if element0.startswith(u"s") and element1.startswith(u"s"):
                id_switch0 = element0.split(u"-")[0]
                id_switch1 = element1.split(u"-")[0]

                port_switch0 = int(link[0].split(u"p")[1])
                port_switch1 = int(link[1].split(u"p")[1])

                
                self.addLink(id_switch0, id_switch1, cls=TCLink, port1 = port_switch0, port2 = port_switch1)
                
            else: #switch and host
                if element0.startswith(u"h"):
                    host = element0
                    switch = element1
                elif element1.startswith(u"h"):
                    host = element1
                    switch = element0
                
                id_switch = switch.split(u"-")[0]
                port_switch = int(switch.split(u"p")[1])

                id_host = host.split(u"-")[0]
                port_host = int(host.split(u"p")[1])

                self.addLink(id_host, id_switch, port1 = port_host, port2 = port_switch, cls=TCLink)

def disable_ipv6(net):
    u""" Disable IPv6 on all hosts and switches """
    for host in net.hosts:
        host.cmd(u"sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        host.cmd(u"sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        host.cmd(u"sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    for switch in net.switches:
        switch.cmd(u"sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        switch.cmd(u"sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        switch.cmd(u"sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    print u"IPv6 disabled on all nodes."


def main(args):
    # Load the all topology info from the JSON file
    with open(args.topology) as f:
        topology_config = json.load(f)

    
    topo = DynamicTopo(topology_config)
    controller = RemoteController(u'c0', ip=u"127.0.0.1")

    net = Mininet(topo=topo, controller=None)
    net.addController(controller)
    net.start()
    disable_ipv6(net)


    while True:
        try:
            reload(interface)  # TO MAKE DEGUG EASIER: Reload the module to reflect any changes, after any choice
            interface.print_menu()
            choice = int(raw_input(u"Enter the number of your choice:"))
            result = interface.main_menu(net, choice)
            if not result:          
                break

        except ValueError:
            print u"Invalid input. Please enter a number."
            continue

    net.stop()


if __name__ == u"__main__":
    parser = argparse.ArgumentParser(description=u'Topology Information')
    parser.add_argument(u'--topology', help=u'JSON file containing the topology configuration, for mininet dinamically \
                        create the topology, it must match netcfg.json',
                        type=unicode, action=u"store", required=False,
                        default=u'/config/topology.json')
    args = parser.parse_args()

    if not os.path.exists(args.topology):
        print u"\nTopology JSON file not found: " + args.topology
        parser.exit(1)


    main(args)
