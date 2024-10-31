/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//#include "include/header.p4"
//#include "include/parser.p4"
//#include "include/checksum.p4"
//#include "include/Ingress.p4"
//#include "include/Egress.p4"
#include "include/define.p4"
#include "include/headers.p4"


/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
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
        transition accept;
    }
    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {


    counter(MAX_SFC_ID, CounterType.packets_and_bytes) ingressSFCCounter;
    action drop() {
        mark_to_drop(standard_metadata);
    }
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
    action sf_action() { // Firewall, NAT, etc... SW can be SF
        hdr.sfc.sc = hdr.sfc.sc - 1; // decrease chain tracker/length
        hdr.sfc_chain.pop_front(1); // Remove used SF

    }
    table sf_processing {
        key = {
            hdr.sfc_chain[0].sf: exact;
        }
        actions = {
            sf_action;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    action sfc_decapsulation() {
           hdr.ethernet.etherType = TYPE_IPV4;
           hdr.ipv4.dscp = 0;
           hdr.sfc.setInvalid();
           hdr.sfc_chain[0].setInvalid();
           hdr.sfc_chain[1].setInvalid();
           hdr.sfc_chain[2].setInvalid();
           hdr.sfc_chain[3].setInvalid();
    }

    action sfc_encapsulation(bit<8> id, bit<8> sc, bit<9> sf1, bit<9> sf2,bit<9> sf3, bit<9> sf4) {
        hdr.ethernet.etherType = TYPE_SFC;
        hdr.sfc.setValid();
        hdr.sfc.id= id;
        hdr.sfc.sc = sc;
        hdr.sfc_chain[0].setValid();
        hdr.sfc_chain[1].setValid();
        hdr.sfc_chain[2].setValid();
        hdr.sfc_chain[3].setValid();
        hdr.sfc_chain[0].sf = sf1; // Too ugly tough.. ASIC does not allow loops
        hdr.sfc_chain[1].sf = sf2;
        hdr.sfc_chain[2].sf = sf3;
        hdr.sfc_chain[3].sf = sf4;
        hdr.sfc_chain[0].tail = 0; // Too ugly tough..
        hdr.sfc_chain[1].tail = 0;
        hdr.sfc_chain[2].tail = 0;
        hdr.sfc_chain[3].tail = 1;
    }
    table sfc_classifier {
        key = {
            hdr.ipv4.dscp: exact;
        }
        actions = {
            sfc_encapsulation;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    action sfc_forward(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    table sfc_egress { // overlay forwarding
        key = {
            hdr.sfc_chain[0].sf: exact;
        }
        actions = {
            sfc_forward;
            drop;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        // ICMP pkts are being parsed and treated as regular ipv4
        if(!hdr.ipv4.isValid()){
            return;
        }

        if (hdr.ipv4.dscp == 0){
            ipv4_lpm.apply();
        }
        else{   // SFC packets (dscp > 0)
            if (!hdr.sfc.isValid()){        // intial stage?
                sfc_classifier.apply();     // Encaps the packet
            }

            sf_processing.apply();          // If this Sw includes SF, just do it.
            ingressSFCCounter.count((bit<32>) hdr.sfc.id);

            if (hdr.sfc.sc == 0){           // SFC ends
                sfc_decapsulation();        //Decaps the packet
                ipv4_lpm.apply();           // Underlay forwarding
            }
            else{
                sfc_egress.apply();         // Overlay forwarding
            }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply { }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.dscp,
              hdr.ipv4.ecn,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.sfc);
        packet.emit(hdr.sfc_chain);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;
