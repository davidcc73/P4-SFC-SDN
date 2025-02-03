#ifndef __DEFINE__
#define __DEFINE__

const bit<8> ETH_HEADER_LEN = 14;
const bit<8> TCP_HEADER_MIN_LEN = 20;   //minimun length is 20 bytes
const bit<8> UDP_HEADER_LEN = 8;
const bit<8> IPV4_MIN_HEAD_LEN = 20;

const bit<8> TYPE_TCP = 0x06;
const bit<8> TYPE_UDP = 0x11;
const bit<8> CLONE_FL_1  = 1;
const bit<8> CLONE_FL_clone3 = 3;
const bit<16> TYPE_IPV4 = 0x800;
const bit<16> ETHERTYPE_ARP = 0X0806;
const bit<16> ETHERTYPE_LLDP = 0x88cc;
const bit<16> ETHERTYPE_LLDP_extra = 0x8942;
const bit<16> TYPE_SFC = 0x1212; // Define TYPE for SFC
const bit<32> MAX_SFC_ID = 1 << 16;
const bit<32> REPORT_MIRROR_SESSION_ID = 100;   //this ones will get to egress do nothing and go back to ingress so later they go to collector

#define IP_VERSION_4 4w4

#define MAX_HOPS 4 //  Max chain length
#define CPU_CLONE_SESSION_ID 99

#define MAX_PORTS 511

//packet type
#define PKT_INSTANCE_TYPE_NORMAL 0
#define PKT_INSTANCE_TYPE_INGRESS_CLONE 1
#define PKT_INSTANCE_TYPE_EGRESS_CLONE 2
#define PKT_INSTANCE_TYPE_COALESCED 3
#define PKT_INSTANCE_TYPE_INGRESS_RECIRC 4
#define PKT_INSTANCE_TYPE_REPLICATION 5
#define PKT_INSTANCE_TYPE_RESUBMIT 6


/* indicate INT by DSCP value */
const bit<6> DSCP_INT = 0x17;
//const bit<6> DSCP_INT = 0x06;
const bit<6> DSCP_MASK = 0x3F;

typedef bit<48> timestamp_t;
typedef bit<32> switch_id_t;

const bit<6> HW_ID = 1;
const bit<8> REPORT_HDR_HOP_LIMIT = 64;//const bit<8> REPORT_HDR_TTL = 64;


#endif