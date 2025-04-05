
from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import os
import random
import time
from mininet.cli import CLI
from datetime import datetime
from io import open

ORANGE = u'\033[38;5;214m'
RED = u'\033[31m'
BLUE = u'\033[34m'
CYAN = u'\033[36m'
GREEN = u'\033[32m'
MAGENTA = u'\033[35m'
PINK = u'\033[38;5;205m'
END = u"\033[0m"

export_file_HIGH = u"HIGH"
export_file_HIGH_EMERGENCY = u"HIGH+EMERGENCY"

host_IPs  = {u"h1": u"10.0.1.1/24", u"h2": u"10.0.2.2/24", u"h3": u"10.0.5.1/24", u"h4": u"10.0.1.2/24"}
intervals = {u"Message": 0.1, u"Audio": 0.1, u"Video": 0.001, u"Emergency": 0.001}       #seconds, used to update the other dictionaries
sizes     = {u"Message": 262, u"Audio": 420, u"Video": 874, u"Emergency": 483}           #bytes

packet_number    = {u"Message": 0, u"Audio": 0, u"Video": 0, u"Emergency": 0}            #placeholder values, updated in update_times()
receiver_timeout = {u"Message": 0, u"Audio": 0, u"Video": 0, u"Emergency": 0}            #placeholder values, updated in update_times(), time receiver will wait for pkts
iteration_sleep  = {u"Message": 0, u"Audio": 0, u"Video": 0, u"Emergency": 0}            #placeholder values, updated in update_times(), time between iterations

num_iterations = 10
iteration_duration_seconds = 5 * 60  #5 minutes, the duration of each iteration of the test
sender_receiver_gap = 1              #seconds to wait for the receiver to start before starting the sender

def update_times():
    global iteration_duration_seconds
    global intervals, packet_number, receiver_timeout, iteration_sleep

    #update the number of packets to be sent in each flow type
    packet_number[u"Message"]   = round(iteration_duration_seconds / (intervals[u"Message"]   + 0.1))
    packet_number[u"Audio"]     = round(iteration_duration_seconds / (intervals[u"Audio"]     + 0.1))
    packet_number[u"Video"]     = round(iteration_duration_seconds / (intervals[u"Video"]     + 0.1))
    packet_number[u"Emergency"] = round(iteration_duration_seconds / (intervals[u"Emergency"] + 0.1))

    receiver_timeout[u"Message"]   = packet_number[u"Message"]   * intervals[u"Message"]   * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout[u"Audio"]     = packet_number[u"Audio"]     * intervals[u"Audio"]     * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout[u"Video"]     = packet_number[u"Video"]     * intervals[u"Video"]     * 1.05  + sender_receiver_gap * 1.05
    receiver_timeout[u"Emergency"] = packet_number[u"Emergency"] * intervals[u"Emergency"] * 1.05  + sender_receiver_gap * 1.05

    iteration_sleep[u"Message"]   = receiver_timeout[u"Message"]   * 1.05
    iteration_sleep[u"Audio"]     = receiver_timeout[u"Audio"]     * 1.05
    iteration_sleep[u"Video"]     = receiver_timeout[u"Video"]     * 1.05
    iteration_sleep[u"Emergency"] = receiver_timeout[u"Emergency"] * 1.05

def create_lock_file(lock_filename):
    lock_file_path = os.path.join(u"/INT/results", lock_filename)

    # Create the lock file if it does not exist
    if not os.path.exists(lock_file_path):
        with open(lock_file_path, u'w') as lock_file:
            lock_file.write(u'') # Write an empty string to the file

def send_packet_script(me, dst_ip, l4, sport, dport, msg, dscp, size, count, interval, export_file, iteration):
    
    command =  "python2 /mininet/tools/send.py --dst_ip " + str(dst_ip) + " --dscp " + str(dscp) + " --l4 " + str(l4) + " --sport " + str(sport) + " --dport " + str(dport) + " --m " + str(msg) + " --s " + str(size) + " --c " + str(count) + " --i " + str(interval)

    if export_file != None:
        command = command + " --export " + str(export_file) + " --me " + str(me.name) + " --iteration " + str(iteration)

    command = command + " >> /INT/results/logs/send-" + str(iteration) + "-" + str(me.name) + ".log"
    command = command + " &"
    #print(f"{me.name} running Command: {command}")
    
    me.cmd(command)

def receive_packet_script(me, export_file, iteration, duration):
    command = "python2 /mininet/tools/receive.py"

    if export_file != None:
        command = command + " --export %s --me %s --iteration %s --duration %s" % (
            export_file, me.name, iteration, duration)

    command = command + " >> /INT/results/logs/receive-%s-%s.log" % (iteration, me.name)
    command = command + " &"
    # print("%s running Command: %s" % (me.name, command))

    me.cmd(command)

def create_Messages_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = u"udp"
    msg = u"INTH1"
    i = intervals[u"Message"]
    size = sizes[u"Message"]
    num_packets = packet_number[u"Message"]

    send_packet_script(me=src_host, dst_ip=dst_IP, l4=l4,
                       sport=sport, dport=dport, msg=msg,
                       dscp=dscp, size=size, count=num_packets,
                       interval=i, export_file=file_results, iteration=iteration)

def create_Audio_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = u"udp"
    msg = u"INTH1"
    i = intervals[u"Audio"]
    size = sizes[u"Audio"]
    num_packets = packet_number[u"Audio"]

    send_packet_script(me=src_host, dst_ip=dst_IP, l4=l4,
                       sport=sport, dport=dport, msg=msg,
                       dscp=dscp, size=size, count=num_packets,
                       interval=i, export_file=file_results, iteration=iteration)

def create_Video_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = u"udp"
    msg = u"INTH1"
    i = intervals[u"Video"]
    size = sizes[u"Video"]
    num_packets = packet_number[u"Video"]

    send_packet_script(me=src_host, dst_ip=dst_IP, l4=l4,
                       sport=sport, dport=dport, msg=msg,
                       dscp=dscp, size=size, count=num_packets,
                       interval=i, export_file=file_results, iteration=iteration)

def create_Emergency_flow(src_host, dst_IP, dscp, sport, dport, file_results, iteration):
    global intervals, packet_number, sizes, host_IPs
    l4 = u"udp"
    msg = u"INTH1"
    i = intervals[u"Emergency"]
    size = sizes[u"Emergency"]
    num_packets = packet_number[u"Emergency"]

    send_packet_script(me=src_host, dst_ip=dst_IP, l4=l4,
                       sport=sport, dport=dport, msg=msg,
                       dscp=dscp, size=size, count=num_packets,
                       interval=i, export_file=file_results, iteration=iteration)

def high_load_test(net, routing):
    global export_file_HIGH
    dport = 443

    utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    rfc3339_time = utc_now.isoformat().replace('+00:00', 'Z')  # Ensure 'Z' for UTC
    print u"---------------------------"
    print GREEN + u"High Load Test, started at:" + unicode(rfc3339_time) + END

    file_results = export_file_HIGH + u"-" + routing + u"_raw_results.csv"
    lock_filename = "LOCK_%s" % file_results

    os.makedirs(u"/INT/results/logs")
    create_lock_file(lock_filename)

    if os.path.exists("/INT/results/%s" % file_results):
        print "Deleting the old results file: %s" % file_results
        os.remove("/INT/results/%s" % file_results)

    h1 = net.get(u"h1")
    h2 = net.get(u"h2")
    h3 = net.get(u"h3")
    h4 = net.get(u"h4")

    h1_dst_IP = host_IPs[h1.name].split(u"/")[0]
    h2_dst_IP = host_IPs[h2.name].split(u"/")[0]
    h3_dst_IP = host_IPs[h3.name].split(u"/")[0]
    h4_dst_IP = host_IPs[h4.name].split(u"/")[0]

    max_receiver_timeout = max(receiver_timeout[u"Message"], receiver_timeout[u"Audio"],
                               receiver_timeout[u"Video"], receiver_timeout[u"Emergency"])
    max_iteration_sleep = max(iteration_sleep[u"Message"], iteration_sleep[u"Audio"],
                              iteration_sleep[u"Video"], iteration_sleep[u"Emergency"])

    sports = random.sample(xrange(49152, 65535), 5)
    print "Sports: %s" % str(sports)

    for iteration in xrange(1, num_iterations + 1):
        print "--------------Starting iteration %s of %s" % (iteration, num_iterations)

        receive_packet_script(h1, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h2, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h3, file_results, iteration, max_receiver_timeout)
        receive_packet_script(h4, file_results, iteration, max_receiver_timeout)

        time.sleep(sender_receiver_gap)

        create_Messages_flow(h1, h3_dst_IP, 0,  sports[0], dport, file_results, iteration)
        create_Messages_flow(h1, h2_dst_IP, 0,  sports[1], dport, file_results, iteration)
        create_Audio_flow(h4, h2_dst_IP, 10, sports[2], dport, file_results, iteration)
        create_Video_flow(h3, h4_dst_IP, 2,  sports[3], dport, file_results, iteration)
        create_Emergency_flow(h2, h1_dst_IP, 51, sports[4], dport, file_results, iteration)

        print "Waiting for %s seconds" % max_iteration_sleep
        time.sleep(max_iteration_sleep)

    utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    rfc3339_time = utc_now.isoformat().replace('+00:00', 'Z')  # Ensure 'Z' for UTC
    print "---------------------------"
    print CYAN + u"High Load Test finished at:" + unicode(rfc3339_time) + END

def print_menu():
    menu = u"""
    ONOS CLI Command Menu:
    ATTENTION: For clean results, delete the contents of the /INT/results directory before starting the tests
    0. Stop Mininet
    1. Mininet CLI
    2. High Load Test
    """
    print menu

def main_menu(net, choice):
    routing = None

    update_times()

    if choice == 0:
        print "Stopping Mininet"
        net.stop()
        return False
    elif choice == 1:
        print "To leave the Mininet CLI, type 'exit' or 'quit'"
        CLI(net)
    elif choice == 2:
        print "Is SFC enabled? input number to choose\n 1- Yes \n 2- No"
        choice2 = raw_input()
        if choice2 == "1":
            routing = "SFC"
        elif choice2 == "2":
            routing = "NO,SFC"
        else:
            print "Invalid choice"
            return True
        high_load_test(net, routing)
    else:
        print "Invalid choice"

    return True
