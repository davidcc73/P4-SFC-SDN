#ifndef __DEPARSER__
#define __DEPARSER__

#include "headers.p4"


/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        // report headers
        packet.emit(hdr.report_ethernet);
        packet.emit(hdr.report_ipv4);
        packet.emit(hdr.report_udp);
        packet.emit(hdr.report_group_header);
        packet.emit(hdr.report_individual_header);

        //ORIGINAL(IPv4 + SFC) PACKET headers
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.sfc);
        packet.emit(hdr.sfc_chain);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);

        // int header
        packet.emit(hdr.intl4_shim);        //extra int data
        packet.emit(hdr.int_header);        //the instructions
        // hop metadata                     //the generated INT statistics at the current hop, captured at parser by hdr.int_data
        packet.emit(hdr.int_switch_id);
        packet.emit(hdr.int_level1_port_ids);
        packet.emit(hdr.int_hop_latency);
        packet.emit(hdr.int_q_occupancy);
        packet.emit(hdr.int_ingress_tstamp);
        packet.emit(hdr.int_egress_tstamp);
        packet.emit(hdr.int_level2_port_ids);
        packet.emit(hdr.int_egress_tx_util);

        // int data
        packet.emit(hdr.int_data);          //the generated INT statistics from the previous hops
    }
}




#endif