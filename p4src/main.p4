/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#include "include/define.p4"
#include "include/headers.p4"
#include "include/parser.p4"
#include "include/deparser.p4"
#include "include/checksum.p4"
#include "include/Ingress.p4"
#include "include/Egress.p4"

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
