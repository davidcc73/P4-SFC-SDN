#ifndef __EGRESS__
#define __EGRESS__

#include "headers.p4"


/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    apply { }
}

#endif