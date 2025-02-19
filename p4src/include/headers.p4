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

//structure to store CPU pkt's metadata for cloning
struct preserving_metadata_CPU_t {
    @field_list(CLONE_FL_clone3)
    bit<9> ingress_port;
    @field_list(CLONE_FL_clone3)
    bit<9> egress_port;
    @field_list(CLONE_FL_clone3)
    bool to_CPU;                 //true when the packet is cloned to CPU/Controller, default is false, so non-CPU cloned packets will still see the correct value (false)
}

//structure to store non-CPU pkt's metadata for cloning
struct preserving_metadata_t {
    @field_list(CLONE_FL_1)
    bit<9> ingress_port;
    @field_list(CLONE_FL_1)
    bit<9> egress_spec;
    @field_list(CLONE_FL_1)
    bit<19> deq_qdepth;
    @field_list(CLONE_FL_1)
    bit<48> ingress_global_timestamp;
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

//---------------------------------------------------------------------------------INT HEADERS
struct int_metadata_t {
    switch_id_t switch_id;
    bit<16> new_bytes;
    bit<8>  new_words;
    bool  source;
    bool  sink;
    bool  transit;
    bit<8> intl4_shim_len;
    bit<16> int_shim_len;
}

// INT shim header for TCP/UDP  (contains addicional INT indormation)
header intl4_shim_t {//32 bits -> 4 byte -> 1 words
    bit<4> int_type;                // Type of INT Header
    bit<2> npt;                     // Next protocol type
    bit<2> rsvd;                    // Reserved
    bit<8> len;                     // (word) Length of INT Metadata header and INT stack in 4-byte words, not including the shim header (1 word)
    bit<6> udp_tcp_ip_dscp;            // depends on npt field. either original dscp, ip protocol or udp dest port
    bit<10> udp_tcp_ip;                // depends on npt field. either original dscp, ip protocol or udp dest port
}
const bit<16> INT_SHIM_HEADER_SIZE = 4;     //bytes

// INT header (contains INT instructions)
header int_header_t { //(96 bits) -> 12 Bytes -> 3 words
    bit<4>   ver;                    // Version
    bit<1>   d;                      // Discard
    bit<1>  e;
    bit<1>  m;
    bit<12>  rsvd;
    bit<5>  hop_metadata_len;        //not used for anything 
    bit<8>  remaining_hop_cnt;       //trigger rule givex x number of hopes, they are decreased but the value is never used
    bit<4>  instruction_mask_0003; /* split the bits for lookup */
    bit<4>  instruction_mask_0407;
    bit<4>  instruction_mask_0811;
    bit<4>  instruction_mask_1215;
    bit<16>  domain_specific_id;     // Unique INT Domain ID
    bit<16>  ds_instruction;         // Instruction bitmap specific to the INT Domain identified by the Domain specific ID
    bit<16>  ds_flags;               // Domain specific flags
}   
const bit<16> INT_HEADER_SIZE = 12;    //bytes
const bit<8> INT_HEADER_WORD = 3;      //words

const bit<16> INT_TOTAL_HEADER_SIZE = INT_HEADER_SIZE + INT_SHIM_HEADER_SIZE;   //bytes


// INT meta-value headers - different header for each value type 32 x 11 = 352 bits == 44 bytes == 11 words
header int_switch_id_t {
    bit<32> switch_id;
}
header int_level1_port_ids_t {
    bit<16> ingress_port_id;
    bit<16> egress_port_id;
}
header int_hop_latency_t {
    bit<32> hop_latency;
}
header int_q_occupancy_t {
    bit<8> q_id;
    bit<24> q_occupancy;
}
header int_ingress_tstamp_t {
    bit<64> ingress_tstamp;
}
header int_egress_tstamp_t {
    bit<64> egress_tstamp;
}
header int_level2_port_ids_t {
    bit<32> ingress_port_id;
    bit<32> egress_port_id;
}
// these one not implemented yet, but is emited
header int_egress_port_tx_util_t {
    bit<32> egress_port_tx_util;
}


header int_data_t {
    // Maximum int metadata stack size in bits: each node adds roughly 44 bytes -> 342 bits of metadata
    // 10260 bits allows for a maximum of 32 nodes in the INT stack
    // (0x3F - 3) * 4 * 8 (excluding INT shim header and INT header)
    varbit<10944> data;
}


// Report Telemetry Headers
header report_group_header_t {
    bit<4>  ver;
    bit<6>  hw_id;
    bit<22> seq_no;
    bit<32> node_id;
}

const bit<8> REPORT_GROUP_HEADER_LEN = 8;

header report_individual_header_t {
    bit<4>  rep_type;
    bit<4>  in_type;
    bit<8>  rep_len;
    bit<8>  md_len;
    bit<1>  d;
    bit<1>  q;
    bit<1>  f;
    bit<1>  i;
    bit<4>  rsvd;
    // Individual report inner contents for Reptype 1 = INT
    bit<16> rep_md_bits;
    bit<16> domain_specific_id;
    bit<16> domain_specific_md_bits;
    bit<16> domain_specific_md_status;
}
const bit<8> REPORT_INDIVIDUAL_HEADER_LEN = 12;

// Telemetry drop report header
header drop_report_header_t {
    bit<32> switch_id;
    bit<16> ingress_port_id;
    bit<16> egress_port_id;
    bit<8>  queue_id;
    bit<8>  drop_reason;
    bit<16> pad;
}
const bit<8> DROP_REPORT_HEADER_LEN = 12;

//---------------------------------------------------------------------------------

struct metadata {                           //clones still have access to the metadata from their "parent" packet
    bit<1> l3_firewall;                     //flag to mark if the current node is a l3_firewall
    bool is_multicast;                      //identify current pkt is multicast
    bool is_multicaster;                    //identify current switch as multicaster
    bit<6> dscp_at_ingress;                 //needed because after decapsulation the DSCP is set to 0 so the pkt is not recapsulated by a switch with hosts
    bit<8> ip_proto;
    bit<8> icmp_type;
    l4_port_t l4_src_port;
    l4_port_t l4_dst_port;
    preserving_metadata_CPU_t perserv_CPU_meta; //to migrate from clone3() to clone_preserving() in the clone_to_CPU scenario

    bool ipv4_update;                           //(OPTIONAL not in use) flag to mark ipv4 header change, leading to the update checksum or not
    bool sfc_forwarded;
    
    int_metadata_t int_meta;                    //used by INT
    preserving_metadata_t perserv_meta;         //used by INT
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

    // INT Report Encapsulation
    ethernet_t                  report_ethernet;
    ipv4_t                      report_ipv4;
    udp_t                       report_udp;

    // INT Headers
    intl4_shim_t                intl4_shim;
    int_header_t                int_header;

    //INT Metadata
    int_switch_id_t             int_switch_id;
    int_level1_port_ids_t       int_level1_port_ids;
    int_hop_latency_t           int_hop_latency;
    int_q_occupancy_t           int_q_occupancy;
    int_ingress_tstamp_t        int_ingress_tstamp;
    int_egress_tstamp_t         int_egress_tstamp;
    int_level2_port_ids_t       int_level2_port_ids;
    int_egress_port_tx_util_t   int_egress_tx_util;
    int_data_t                  int_data;               //all the INT stack data from previous hopes

    //INT Report Headers
    report_group_header_t       report_group_header;
    report_individual_header_t  report_individual_header;
    drop_report_header_t        drop_report_header;
}


#endif