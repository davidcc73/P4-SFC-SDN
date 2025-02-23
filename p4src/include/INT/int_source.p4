/* -*- P4_16 -*- */
control process_int_set_source (inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    action int_set_source () {
        meta.int_meta.source = true;
    }

    table tb_set_source {
        key = {
            standard_metadata.ingress_port: exact;
        }
        actions = {
            int_set_source;
            NoAction();
        }
        const default_action = NoAction();
        size = MAX_PORTS;
    }

    apply {
        tb_set_source.apply();
    }
}

control process_int_set_sink (inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    action int_set_sink () {
        meta.int_meta.sink = true;
    }

    table tb_set_sink {
        key = {
            standard_metadata.egress_spec: exact;    //it will be invoked at ingress, so egress_spec is the next hop, egress_port will be 0 until egress
        }
        actions = {
            int_set_sink;
            NoAction();
        }
        const default_action = NoAction();
        size = MAX_PORTS;
    }

    apply {
        tb_set_sink.apply();
    }
}

// Insert INT header to the packet
control process_int_source (inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    action int_source(bit<5> hop_metadata_len, bit<8> remaining_hop_cnt, bit<4> ins_mask0003, bit<4> ins_mask0407) {
        // insert INT shim header
        hdr.intl4_shim.setValid();                              
        hdr.intl4_shim.int_type = 1;                            // int_type: Hop-by-hop type (1) , destination type (2), MX-type (3)
        hdr.intl4_shim.npt = 0;                                 // next protocol type: 0
        hdr.intl4_shim.len = INT_HEADER_WORD;                   // This is 3 from 0xC (INT_TOTAL_HEADER_SIZE >> 2)
        hdr.intl4_shim.udp_tcp_ip_dscp = hdr.ipv4.dscp;        
        hdr.intl4_shim.udp_tcp_ip = 0;                     
        
        // insert INT header
        hdr.int_header.setValid();
        hdr.int_header.ver = 2;
        hdr.int_header.d = 0;
        hdr.int_header.e = 0;
        hdr.int_header.m = 0;
        hdr.int_header.rsvd = 0;
        hdr.int_header.hop_metadata_len = hop_metadata_len;
        hdr.int_header.remaining_hop_cnt = remaining_hop_cnt;
        hdr.int_header.instruction_mask_0003 = ins_mask0003;
        hdr.int_header.instruction_mask_0407 = ins_mask0407;
        hdr.int_header.instruction_mask_0811 = 0; // not supported
        hdr.int_header.instruction_mask_1215 = 0; // not supported

        hdr.int_header.domain_specific_id = 0;                  // Unique INT Domain ID
        hdr.int_header.ds_instruction = 0;                      // Instruction bitmap specific to the INT Domain identified by the Domain specific ID
        hdr.int_header.ds_flags = 0;                            // Domain specific flags

        // add the header len (3 words) to total len
        hdr.ipv4.totalLen = hdr.ipv4.totalLen + INT_TOTAL_HEADER_SIZE;          //len at IPv4 contains everything, including base IPv4 header
        //hdr.ipv6.payload_len = hdr.ipv6.payload_len + INT_TOTAL_HEADER_SIZE;  //payload_len at IPv6 contains everything, excluding base IPv6 header
        if(hdr.udp.isValid()) {
            hdr.udp.len = hdr.udp.len + INT_TOTAL_HEADER_SIZE;   
        }
        
        hdr.ipv4.dscp = DSCP_INT;
    }

    table tb_int_source {
        key = {
            //configure for each flow type to be monitored (HTTP, SQL, etc)
            // 4 fields identifying flow
            //include ip src, udp/tcp src and dest too
            hdr.ipv4.srcAddr: ternary;
            hdr.ipv4.dstAddr: ternary;
            meta.l4_src_port: ternary;
            meta.l4_dst_port: ternary;
        }
        actions = {
            int_source;
            NoAction;
        }
        const default_action = NoAction();
    }

    apply {        
        tb_int_source.apply();
    }
}
