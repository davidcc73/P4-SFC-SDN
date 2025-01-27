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
        mark_to_drop(standard_metadata);                           //changes egress_spec to special value, so pkt is dropped at Ingrees' end
    }

    action ipv4_forward(macAddr_t dstAddr) {
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
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
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
        log_msg("Doing SFC Decapsulation");
        hdr.ethernet.etherType = TYPE_IPV4;
        hdr.ipv4.dscp = 0;                     //avoids re-encapsulations on nodes that can encapsulate
        hdr.sfc.setInvalid();
        hdr.sfc_chain[0].setInvalid();
        hdr.sfc_chain[1].setInvalid();
        hdr.sfc_chain[2].setInvalid();
        hdr.sfc_chain[3].setInvalid();
    }

    action sfc_encapsulation(bit<8> id, bit<8> sc, bit<9> sf1, bit<9> sf2,bit<9> sf3, bit<9> sf4) {
        log_msg("Doing SFC Encapsulation");
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

    action set_egress_port(egressSpec_t port) {          //set the egress port, using the dst mac address
        standard_metadata.egress_spec = port;
    }
    table unicast {
        key = {
            hdr.ethernet.dstAddr: lpm;
        }
        actions = {
            set_egress_port;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table multicaster {
        key = {
            1w1: exact;    //dummy key of value 1
        }
        actions = {
            NoAction;
        }
        default_action = NoAction();
    }

    action set_dst_addr(ip4Addr_t ip, macAddr_t mac) {
        log_msg("Dst MAC addr set to:{}", {mac});
        log_msg("Dst IP addr set to:{}", {ip});
        hdr.ethernet.dstAddr = mac;
        hdr.ipv4.dstAddr = ip;
    }
    table multicast_dst_addr {         
        key = {
            meta.dscp_at_ingress: exact;        //in case of SFC decap, the header dscp is 0
        }
        actions = {
            set_dst_addr;
            NoAction;
        }
        default_action = NoAction();
    }

    action set_multicast_group(group_id_t gid) {
        log_msg("Multicast group set to:{}", {gid});
        standard_metadata.mcast_grp = gid;
        meta.is_multicast = true;
    }
    table multicast {                       // each multicast address will represent a group
        key = {
            hdr.ethernet.dstAddr: lpm;
        }
        actions = {
            set_multicast_group;
            NoAction;
        }
        default_action = NoAction();
    }

    /*
     * ACL table  and actions.
     * Clone the packet to the CPU (PacketIn) or drop.
     */
    action clone_to_cpu() {
        meta.perserv_CPU_meta.ingress_port = standard_metadata.ingress_port;
        meta.perserv_CPU_meta.egress_port = CPU_PORT;                         //the packet only gets the egress right before egress, so we use CPU_PORT value
        meta.perserv_CPU_meta.to_CPU = true;
        clone_preserving_field_list(CloneType.I2E, CPU_CLONE_SESSION_ID, CLONE_FL_clone3);
    }

    direct_counter(CounterType.packets_and_bytes) acl_counter;
    table acl {
        key = {
            standard_metadata.ingress_port: ternary;
            hdr.ethernet.dstAddr: ternary;
            hdr.ethernet.srcAddr: ternary;
            hdr.ethernet.etherType: ternary;
            meta.ip_proto: ternary;
            meta.icmp_type: ternary;
            meta.l4_src_port: ternary;
            meta.l4_dst_port: ternary;
        }
        actions = {
            clone_to_cpu;
            drop;
        }
        counters = acl_counter;
    }

    apply {
        //---------------------------------------------------------------------------LLDP SUpport
        if (hdr.packet_out.isValid()) {
            standard_metadata.egress_spec = hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
            exit;
        }

        acl.apply();            //Pkt may be cloned to CPU
        //---------------------------------------------------------------------------

        // ICMP pkts are being parsed and treated as regular ipv4
        meta.dscp_at_ingress = hdr.ipv4.dscp;
        
        //---------------SFC
        if (hdr.ipv4.dscp != 0){
        
            // SFC packets (dscp > 0)
            if (!hdr.sfc.isValid()){        // intial stage?
                sfc_classifier.apply();     // Encaps the packet
            }

            sf_processing.apply();          // If this Sw includes SF, just do it.
            ingressSFCCounter.count((bit<32>) hdr.sfc.id);

            if(meta.l3_firewall == 1){               // If this node is a l3_fireWall, do it
                if(!l3_fireWall.apply().hit){        // the packet is marked to be droped, just do not do l2_forwarding, beacuse we should not change the egress_spec special value
                    log_msg("Pkt blocked by firewall");
                    return;                          // finish the Ingress processing
                }
            }

            if (hdr.sfc.sc != 0){           //L2 Forwarding using SFC
                log_msg("Trying SFC forwarding");
                sfc_egress.apply();         // Overlay forwarding
                return;
            }
            else{                           // SFC ends
                sfc_decapsulation();        // Decaps the packet    
            }
        }
        
        //--------------------------------- L3+L2 Forwarding (IP -> Set the egress_spec)---------------------------------
        if(multicaster.apply().hit){      // If the multicaster change the dst addresses to multicast
            log_msg("Trying to change pkt to multicast");
            multicast_dst_addr.apply();   // meta.dscp_at_ingress -> dst_addr (both ethernet and IP) (in case of SFC decap, the header dscp is 0)
        }

        if(ipv4_lpm.apply().hit){  // Unicast Forwarding L3: dst IP -> dst ethernet
            unicast.apply();       // L2: dst ethernet -> ports
        }
        else{
            log_msg("Unicast failed. Trying Multicast");
            if(!multicast.apply().hit){   // Multicast Forwarding (based on the dstAddr, sets mcast_grp)
                log_msg("Multicast failed, droping pkt");
                drop();                   // can not do uni or multicast, just drop
            }
        }
    }
}


#endif


// pacote ja vem com unicast addrs, at s3 depending on the DSCP we change to the addr of the group we want, fazer a decisao antes do desencapsualmento estara sempre a 0
//set group multicast e seus ports em cada switch pelo net.cfg
//DSCP (nó especial, manipula para passar a ser multicast) -> DST ADDR ETH/IP    -> MULTICAST GROUP e PORT   esta ultima transição é feita pelo proprio straum (n consigo fazer manualmente por ONOS) 
//o mais correto seria ter o ONOS  a fazer os grupos multicast e a dizer ao switch qual o porto associado a cada grupo de forma automatica e escalavel
//no noss cenario com o ONSO a so fazer push de regras antigas, so vamos ate aos addresses multicast e depois mapeamos diretamente para os portos de forma manual e estatica