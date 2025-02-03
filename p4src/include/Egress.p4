#ifndef __EGRESS__
#define __EGRESS__

#include "headers.p4"

#include "INT/int_transit.p4"
#include "INT/int_sink.p4"

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    apply { 
        //-----------------Restore packet standard_metadata from clones
        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE){
            if(meta.perserv_CPU_meta.to_CPU == true) {
                log_msg("Detected clone meant to CPU");
                // restore the standard_metadata values that were perserved by the clone_preserving_field_list
                standard_metadata.egress_port = meta.perserv_CPU_meta.egress_port;
                standard_metadata.ingress_port = meta.perserv_CPU_meta.ingress_port;
            }
            else { //it is the only other pkt that we clone
                log_msg("Detected report clone");
                //-------------Restore data from the clone, prepare info for report
                standard_metadata.ingress_port = meta.perserv_meta.ingress_port;
                standard_metadata.deq_qdepth = meta.perserv_meta.deq_qdepth;
                standard_metadata.ingress_global_timestamp = meta.perserv_meta.ingress_global_timestamp;
            }
        }
        //-----------------Standard packet forwarding
        if (standard_metadata.egress_port == CPU_PORT) {
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;		
        }
        if (meta.is_multicast == true && standard_metadata.ingress_port == standard_metadata.egress_port) {   //avoid multicast loops
            mark_to_drop(standard_metadata);
            return;
        }
        
        //-----------------INT processing portion
        if(hdr.int_header.isValid()) {
            log_msg("adding my INT stats");
            process_int_transit.apply(hdr, meta, standard_metadata);   //(transit) INFO ADDED TO PACKET AT DEPARSER

            if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE) {   //prepare report
                // create int report 
                log_msg("creating INT report");
                process_int_report.apply(hdr, meta, standard_metadata);

            }else if (meta.int_meta.sink == true) {                           //restore packet to original state
                log_msg("restoring packet to original state");
                process_int_sink.apply(hdr, meta, standard_metadata);
            }
        }
    }
}

#endif