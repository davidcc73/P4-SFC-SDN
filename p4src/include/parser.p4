#ifndef __PARSER__
#define __PARSER__

#include "headers.p4"
#include "define.p4"

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition select(standard_metadata.ingress_port) {
            CPU_PORT: parse_packet_out;
            default: parse_ethernet;
        }
    }

    state parse_packet_out {
        packet.extract(hdr.packet_out);
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_SFC: parse_sfc;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_sfc {
        packet.extract(hdr.sfc);
        transition parse_sfc_chain;
    }
    state parse_sfc_chain {
        packet.extract(hdr.sfc_chain.next);
        transition select(hdr.sfc_chain.last.tail) {
            1: parse_ipv4;
            default: parse_sfc_chain;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_TCP: parse_tcp;
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        meta.l4_src_port = hdr.tcp.srcPort;
        meta.l4_dst_port = hdr.tcp.dstPort;
        transition select(hdr.ipv4.dscp) {
            DSCP_INT &&& DSCP_MASK: parse_intl4_shim;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        meta.l4_src_port = hdr.udp.srcPort;
        meta.l4_dst_port = hdr.udp.dstPort;
        transition select(hdr.ipv4.dscp) {
            DSCP_INT &&& DSCP_MASK: parse_intl4_shim;
            default: accept;
        }
    }

    state parse_intl4_shim {
        packet.extract(hdr.intl4_shim);
        meta.int_meta.intl4_shim_len = hdr.intl4_shim.len;  //all INT but shim not included
        transition parse_int_header;
    }

    state parse_int_header {
        packet.extract(hdr.int_header); //parse INT instructions
        transition parse_int_data;
    }

    state parse_int_data {
        // Parse INT metadata stack, extract into int_data a certain amount bits (all before body), convertion from word to bits
        packet.extract(hdr.int_data, ((bit<32>) (meta.int_meta.intl4_shim_len - INT_HEADER_WORD)) * 32); 
        transition accept;
    }
}


#endif