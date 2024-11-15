#ifndef __INGRESS__
#define __INGRESS__

#include "headers.p4"
#include "define.p4"



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
    action sf_action(bit<1> fireWall) { // Firewall, NAT, etc... SW can be SF
        hdr.sfc.sc = hdr.sfc.sc - 1; // decrease chain tracker/length
        hdr.sfc_chain.pop_front(1); // Remove used SF
        
        meta.l3_firewall = fireWall;       // Flag current node as being Firewall or not
    }
    table sf_processing {
        key = {
            hdr.sfc_chain[0].sf: exact;       //it's the id of the current node, causing the pop in the SFC stack (to simulate processing). NOT DONE NOW: if not trigered, we keep doing SFC forwarding.
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
        hdr.ipv4.dscp = 0;                     //avoids re-encapsulations on nodes that can encapsulate
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
        hdr.sfc_chain[3].sf = sf4; //this means at the most we can do visit 4 SFs
        hdr.sfc_chain[0].tail = 0; // Too ugly tough..   This are never used!
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
            hdr.sfc_chain[0].sf: exact;             //id of the next node in the chain, loop to self is not implemented in the P4 code
        }
        actions = {
            sfc_forward;
            drop;
        }
        size = 1024;
        default_action = drop();
    }

    table l3_fireWall {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            drop;
            NoAction;
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

            if(meta.l3_firewall == 1){     // If this node is a l3_fireWall, do it
                l3_fireWall.apply()
            }

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


#endif