#ifndef __DEFINE__
#define __DEFINE__


const bit<8> TYPE_TCP = 0x06;
const bit<8> TYPE_UDP = 0x11;
const bit<8> CLONE_FL_clone3 = 3;
const bit<16> TYPE_IPV4 = 0x800;
const bit<16> ETHERTYPE_ARP = 0X0806;
const bit<16> ETHERTYPE_LLDP = 0x88cc;
const bit<16> ETHERTYPE_LLDP_extra = 0x8942;
const bit<16> TYPE_SFC = 0x1212; // Define TYPE for SFC
const bit<32> MAX_SFC_ID = 1 << 16;

//packet type
#define PKT_INSTANCE_TYPE_NORMAL 0
#define PKT_INSTANCE_TYPE_INGRESS_CLONE 1
#define PKT_INSTANCE_TYPE_EGRESS_CLONE 2
#define PKT_INSTANCE_TYPE_COALESCED 3
#define PKT_INSTANCE_TYPE_INGRESS_RECIRC 4
#define PKT_INSTANCE_TYPE_REPLICATION 5
#define PKT_INSTANCE_TYPE_RESUBMIT 6

#define MAX_HOPS 4 //  Max chain length
#define CPU_CLONE_SESSION_ID 99



#endif