/* -*- P4_16 -*- */

control process_int_sink (inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    action int_sink() {
        // restore original headers
       
        //INT specification says that the Traffic classe field should be restored, it was used to signal the usage of INT
        hdr.ipv4.dscp = hdr.intl4_shim.udp_tcp_ip_dscp;
        
        // restore length fields of IPv4 header and UDP header, remove INT shim, instruction, and data
        bit<16> len_bytes = (((bit<16>)hdr.intl4_shim.len) * 4) + INT_SHIM_HEADER_SIZE;
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - len_bytes;
        if(hdr.udp.isValid()) {
            hdr.udp.len = hdr.udp.len - len_bytes;
        }

        // remove all the INT information from the packet
        hdr.intl4_shim.setInvalid();
        hdr.int_header.setInvalid();

        hdr.int_switch_id.setInvalid();
        hdr.int_level1_port_ids.setInvalid();
        hdr.int_hop_latency.setInvalid();
        hdr.int_q_occupancy.setInvalid();
        hdr.int_ingress_tstamp.setInvalid();
        hdr.int_egress_tstamp.setInvalid();
        hdr.int_level2_port_ids.setInvalid();
        hdr.int_egress_tx_util.setInvalid();

        hdr.int_data.setInvalid();
    }

    table tb_int_sink {
        actions = {
            int_sink;
        }
        default_action = int_sink();
    }

    apply {
        tb_int_sink.apply();
    }
}

control process_int_report (inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    register<bit<22>>(1) seq_number;
    /********************** A C T I O N S **********************/

    action increment_counter() {
        bit<22> tmp;
        seq_number.read(tmp, 0);
        tmp = tmp + 1;
        seq_number.write(0, tmp);
    }

    action do_report_encapsulation( macAddr_t src_mac, 
                                    macAddr_t mon_mac, 
                                    ip4Addr_t src_ip,
                                    ip4Addr_t mon_ip, 
                                    l4_port_t mon_port) {
        // INT Raport structure
        // [Eth][IPv4][UDP][INT RAPORT HDR][ETH][IPv4][UDP/TCP][INT HDR][INT DATA]
        //Report Ethernet Header
        hdr.report_ethernet.setValid();
        hdr.report_ethernet.dstAddr = mon_mac;
        hdr.report_ethernet.srcAddr = src_mac;
        hdr.report_ethernet.etherType = TYPE_IPV4;


        bit<8> used_protocol_len = 0;
             if(hdr.udp.isValid()){used_protocol_len = UDP_HEADER_LEN;}
        else if(hdr.tcp.isValid()){used_protocol_len = TCP_HEADER_MIN_LEN;}   //if option flags are used the size will vary
        //Report IPV4 Header
        hdr.report_ipv4.setValid();
        hdr.report_ipv4.version = IP_VERSION_4;
        hdr.report_ipv4.dscp = 6w0;
        hdr.report_ipv4.ecn = 2w0;
        //hdr.report_ipv4.flow_label = 20w0;     //20w0 here is just a placeholder
        
        // The same length but for ipv4, the base header length does count for the payload length
        hdr.report_ipv4.totalLen =   (bit<16>) IPV4_MIN_HEAD_LEN +   //self size
                                        (bit<16>) UDP_HEADER_LEN + 
                                        (bit<16>) REPORT_GROUP_HEADER_LEN +
                                        (bit<16>) REPORT_INDIVIDUAL_HEADER_LEN +
                                        (bit<16>) ETH_HEADER_LEN + 
                                        (bit<16>) IPV4_MIN_HEAD_LEN + 
                                        (bit<16>) used_protocol_len +                                //it will vary depending on the used protocol and options
                                        INT_SHIM_HEADER_SIZE + (((bit<16>) hdr.intl4_shim.len) * 4); //convert from word to bytes

        hdr.report_ipv4.protocol = TYPE_UDP;        // a 32-bit unsigned number with hex value 11 (UDP)
        hdr.report_ipv4.ttl = REPORT_HDR_HOP_LIMIT;
        hdr.report_ipv4.srcAddr = src_ip;
        hdr.report_ipv4.dstAddr = mon_ip;





        //Report UDP Header
        hdr.report_udp.setValid();
        hdr.report_udp.checksum = 1;            //placeholder value
        hdr.report_udp.srcPort = 1234;
        hdr.report_udp.dstPort = mon_port;
        hdr.report_udp.len = (bit<16>) UDP_HEADER_LEN + 
                                 (bit<16>) REPORT_GROUP_HEADER_LEN +
                                 (bit<16>) REPORT_INDIVIDUAL_HEADER_LEN +
                                 (bit<16>) ETH_HEADER_LEN + 
                                 (bit<16>) IPV4_MIN_HEAD_LEN + 
                                 (bit<16>) used_protocol_len +
                                 INT_SHIM_HEADER_SIZE + (((bit<16>) hdr.intl4_shim.len) * 4);
        
        hdr.report_group_header.setValid();
        hdr.report_group_header.ver = 2;
        hdr.report_group_header.hw_id = HW_ID;
        seq_number.read(hdr.report_group_header.seq_no, 0);
        increment_counter();
        hdr.report_group_header.node_id = meta.int_meta.switch_id;

        /* Telemetry Report Individual Header */
        hdr.report_individual_header.setValid();
        hdr.report_individual_header.rep_type = 1;
        hdr.report_individual_header.in_type = 3;
        hdr.report_individual_header.rep_len = 0;
        hdr.report_individual_header.md_len = 0;
        hdr.report_individual_header.d = 0;
        hdr.report_individual_header.q = 0;
        hdr.report_individual_header.f = 1;
        hdr.report_individual_header.i = 0;
        hdr.report_individual_header.rsvd = 0;

        /* Individual report inner contents */

        hdr.report_individual_header.rep_md_bits = 0;
        hdr.report_individual_header.domain_specific_id = 0;
        hdr.report_individual_header.domain_specific_md_bits = 0;
        hdr.report_individual_header.domain_specific_md_status = 0;

        /*Restoring the original DSCP value at the original IPv4 header (It was change to signal the usage of INT)*/
        hdr.ipv4.dscp = hdr.intl4_shim.udp_tcp_ip_dscp;

        //cut out the OG packet body, only the  headers remain
        truncate((bit<32>)hdr.report_ipv4.totalLen + (bit<32>) ETH_HEADER_LEN);   
    }

    table tb_generate_report {
        key = {              //needs at least a key
            1w0 : exact;    //dummy key to trigger the action
        }
        actions = {
            do_report_encapsulation;
            NoAction();
        }
        default_action = NoAction();
    }

    apply {
        tb_generate_report.apply();
    }
}
