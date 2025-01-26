#ifndef __EGRESS__
#define __EGRESS__

#include "headers.p4"


/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    apply { 

        if(hdr.ethernet.etherType == ETHERTYPE_LLDP){
            log_msg("DETETEI NA ENGRESS PKT LLDP");
        }
        if(hdr.ethernet.etherType == ETHERTYPE_ARP){
            log_msg("DETETEI NA EGRESS PKT ARP");
        }
        //-----------------Restore packet standard_metadata from clones
        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE){
            if(meta.perserv_CPU_meta.to_CPU == true) {
                // restore the standard_metadata values that were perserved by the clone_preserving_field_list
                standard_metadata.egress_port = meta.perserv_CPU_meta.egress_port;
                standard_metadata.ingress_port = meta.perserv_CPU_meta.ingress_port;
            }
        }
        //-----------------Standard packet forwarding
        if (standard_metadata.egress_port == CPU_PORT) {
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;		
        }
        if (meta.is_multicast == true && standard_metadata.ingress_port == standard_metadata.egress_port) {   //avoid multicast loops
            mark_to_drop(standard_metadata);
        }
    }
}

#endif