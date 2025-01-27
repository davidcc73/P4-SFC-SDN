#ifndef __HEADERS__
#define __HEADERS__

#include "define.p4"

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<9>   port_num_t;    //added as part of having Controller
typedef bit<16> group_id_t;
typedef bit<16> l4_port_t;

struct preserving_metadata_CPU_t {
    @field_list(CLONE_FL_clone3)
    bit<9> ingress_port;
    @field_list(CLONE_FL_clone3)
    bit<9> egress_port;
    @field_list(CLONE_FL_clone3)
    bool to_CPU;                 //true when the packet is cloned to CPU/Controller, default is false, so non-CPU cloned packets will still have see the correct value (false)
}

//added as part of having Controller
@controller_header("packet_in")
header packet_in_header_t {
    port_num_t ingress_port;
    bit<7> _pad;
}
//added as part of having Controller
@controller_header("packet_out")
header packet_out_header_t {
    port_num_t egress_port;
    bit<7> _pad;
}


header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header sfc_t {
    bit<8> id;
    bit<8> sc; // Chain tracker (number of nodes, including encapsulation, no matter where, if 0 decapsulate)
}

header sfc_chain_t {
    bit<9> sf; // Next SF
    bit<7> tail; // 1: Tail
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp; // 0: Normal, 1~ : SFC     TOS is dscp++ecn
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> len;
    bit<16> checksum;

}

struct metadata {
    bit<1> l3_firewall;                     //flag to mark if the current node is a l3_firewall
    bool is_multicast;                      //id multicast pkts
    bit<6> dscp_at_ingress;                 //needed because after decapsulation the DSCP is set to 0 so the pkt is not recapsulated by a switch with hosts
    bit<8> ip_proto;
    bit<8> icmp_type;
    l4_port_t l4_src_port;
    l4_port_t l4_dst_port;
    preserving_metadata_CPU_t perserv_CPU_meta; //to migrate from clone3() to clone_preserving() in the clone_to_CPU scenario
}

struct headers {
    packet_in_header_t packet_in;
    ethernet_t ethernet;
    sfc_t sfc;
    sfc_chain_t[MAX_HOPS] sfc_chain;
    ipv4_t ipv4;
    tcp_t tcp;
    udp_t udp;

    packet_out_header_t packet_out;
}


#endif