-- Return a slice of a table
function table_slice(input_table, first, last)
    local subtable = {}
    for i = first, last do
      subtable[#subtable + 1] = input_table[i]
    end
    return subtable
end
  
-- Convert a number to bits
function tobits(number, bitcount, first_bit, last_bit)
    local bit_table = {}
    for bit_index = bitcount, 1, -1 do
        remainder = math.fmod(number, 2)
        bit_table[bit_index] = remainder
        number = (number - remainder) / 2
    end
    return table.concat(table_slice(bit_table, first_bit, last_bit))
end

p4_proto = Proto("p4-int_report_RPires","P4-INT_REPORT Protocol")
p4_int_proto = Proto("p4-int_header", "P4-INT_HEADER Protocol")

function p4_proto.dissector(buffer,pinfo,tree)
    pinfo.cols.protocol = "P4-INT REPORT"
    local subtree_report = tree:add(p4_proto,buffer(),"Telemetry Report")
    subtree_report:add(buffer(0,1), "ver (4 bits) - Binary: " .. tobits(buffer(0,1):uint(), 8, 1, 4))

    -- Change offset positions for IPv6
    subtree_report:add(buffer(22,16), "src_addr (128 bits) - " .. string.format("%x:%x:%x:%x:%x:%x:%x:%x",
                                                                buffer(22,2):bitfield(0, 16), buffer(24,2):bitfield(0, 16),
                                                                buffer(26,2):bitfield(0, 16), buffer(28,2):bitfield(0, 16),
                                                                buffer(30,2):bitfield(0, 16), buffer(32,2):bitfield(0, 16),
                                                                buffer(34,2):bitfield(0, 16), buffer(36,2):bitfield(0, 16)))
    subtree_report:add(buffer(38,16), "dst_addr (128 bits) - " .. string.format("%x:%x:%x:%x:%x:%x:%x:%x",
                                                                buffer(38,2):bitfield(0, 16), buffer(40,2):bitfield(0, 16),
                                                                buffer(42,2):bitfield(0, 16), buffer(44,2):bitfield(0, 16),
                                                                buffer(46,2):bitfield(0, 16), buffer(48,2):bitfield(0, 16),
                                                                buffer(50,2):bitfield(0, 16), buffer(52,2):bitfield(0, 16)))

    subtree_report:add(buffer(54,2), "src_port (16 bits) - " .. string.format("%d", buffer(54,2):bitfield(0, 16)))
    subtree_report:add(buffer(56,2), "dst_port (16 bits) - " .. string.format("%d", buffer(56,2):bitfield(0, 16)))

    -- Adjust offset positions for other fields accordingly
    subtree_report:add(buffer(80,2), "Hop4 switch ID (16 bits) - - - - - - - - " .. string.format("%d", buffer(80,2):bitfield(0, 16)))
    subtree_report:add(buffer(82,2), "Hop4 l1 ingress port (16 bits) - " .. string.format("%d", buffer(82,2):bitfield(0, 16)))
    subtree_report:add(buffer(84,2), "Hop4 l1 egress port (16 bits) - " .. string.format("%d", buffer(84,2):bitfield(0, 16)))
    subtree_report:add(buffer(88,2), "Hop4 latency (16 bits) - " .. string.format("%d", buffer(88,2):bitfield(0, 16)))
    subtree_report:add(buffer(92,2), "Hop4 queue size (16 bits) - " .. string.format("%d", buffer(92,2):bitfield(0, 16)))
    subtree_report:add(buffer(112,2), "Hop4 l2 ingress port (16 bits) - " .. string.format("%d", buffer(112,2):bitfield(0, 16)))
    subtree_report:add(buffer(116,2), "Hop4 l2 egress port (16 bits) - " .. string.format("%d", buffer(116,2):bitfield(0, 16)))


    subtree_report:add(buffer(80,2), "Hop3 switch ID (16 bits) - - - - - - - - " .. string.format("%d", buffer(80,2):bitfield(0, 16)))
    subtree_report:add(buffer(82,2), "Hop3 l1 ingress port (16 bits) - " .. string.format("%d", buffer(82,2):bitfield(0, 16)))
    subtree_report:add(buffer(84,2), "Hop3 l1 egress port (16 bits) - " .. string.format("%d", buffer(84,2):bitfield(0, 16)))
    subtree_report:add(buffer(88,2), "Hop3 latency (16 bits) - " .. string.format("%d", buffer(88,2):bitfield(0, 16)))
    subtree_report:add(buffer(92,2), "Hop3 queue size (16 bits) - " .. string.format("%d", buffer(92,2):bitfield(0, 16)))
    subtree_report:add(buffer(112,2), "Hop3 l2 ingress port (16 bits) - " .. string.format("%d", buffer(112,2):bitfield(0, 16)))
    subtree_report:add(buffer(116,2), "Hop3 l2 egress port (16 bits) - " .. string.format("%d", buffer(116,2):bitfield(0, 16)))


    subtree_report:add(buffer(124,2), "Hop2 switch ID (16 bits) - - - - - - - - " .. string.format("%d", buffer(124,2):bitfield(0, 16)))
    subtree_report:add(buffer(126,2), "Hop2 l1 ingress port (16 bits) - " .. string.format("%d", buffer(126,2):bitfield(0, 16)))
    subtree_report:add(buffer(128,2), "Hop2 l1 egress port (16 bits) - " .. string.format("%d", buffer(128,2):bitfield(0, 16)))
    subtree_report:add(buffer(132,2), "Hop2 latency (16 bits) - " .. string.format("%d", buffer(132,2):bitfield(0, 16)))
    subtree_report:add(buffer(136,2), "Hop2 queue size (16 bits) - " .. string.format("%d", buffer(136,2):bitfield(0, 16)))
    subtree_report:add(buffer(156,2), "Hop2 l2 ingress port (16 bits) - " .. string.format("%d", buffer(156,2):bitfield(0, 16)))
    subtree_report:add(buffer(160,2), "Hop2 l2 egress port (16 bits) - " .. string.format("%d", buffer(160,2):bitfield(0, 16)))


    subtree_report:add(buffer(168,2), "Hop1 switch ID (16 bits) - - - - - - - - " .. string.format("%d", buffer(168,2):bitfield(0, 16)))
    subtree_report:add(buffer(170,2), "Hop1 l1 ingress port (16 bits) - " .. string.format("%d", buffer(170,2):bitfield(0, 16)))
    subtree_report:add(buffer(172,2), "Hop1 l1 egress port (16 bits) - " .. string.format("%d", buffer(172,2):bitfield(0, 16)))
    subtree_report:add(buffer(176,2), "Hop1 latency (16 bits) - " .. string.format("%d", buffer(176,2):bitfield(0, 16)))
    subtree_report:add(buffer(180,2), "Hop1 queue size (16 bits) - " .. string.format("%d", buffer(180,2):bitfield(0, 16)))
    subtree_report:add(buffer(200,2), "Hop1 l2 ingress port (16 bits) - " .. string.format("%d", buffer(200,2):bitfield(0, 16)))
    subtree_report:add(buffer(204,2), "Hop1 l2 egress port (16 bits) - " .. string.format("%d", buffer(204,2):bitfield(0, 16)))
  end

my_table = DissectorTable.get("udp.port")
my_table:add(1234, p4_proto)
