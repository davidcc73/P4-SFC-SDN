
# Define the directory path
import os
import pprint

from influxdb import InfluxDBClient

result_directory = "results"
final_file = "final_results.xlsx"
current_directory = os.path.dirname(os.path.abspath(__file__)) 

parent_path = os.path.abspath(os.path.join(current_directory, ".."))
results_path = os.path.join(parent_path, result_directory) 
final_file_path = os.path.join(results_path, final_file) 

args = None
results = {}

num_switches = 5           #switches ids go from 1 to 5

# Define DB connection parameters
host='localhost'
dbname='int'
# Connect to the InfluxDB client
client = InfluxDBClient(host=host, database=dbname)

algorithms = None
test_cases = None

last_line_data = 0              #last line of raw data in the file

headers_lines = ["AVG Out of Order Packets (Nº)", "AVG Packet Loss (Nº)", "AVG Packet Loss (%)", 
                "AVG 1º Packet Delay (nanoseconds)", 

                "AVG Flow Jitter (nanoseconds)", "STD Flow Jitter (nanoseconds)",
                "AVG Flows Latency (nanoseconds)", "STD Flows Latency (nanoseconds)", 
                "AVG Hop Latency (nanoseconds)", "STD Hop Latency (nanoseconds)",

                "AVG of packets to each switch (%)", 
                "Standard Deviation of packets to each switch (%)", 

                "AVG of processed Bytes to each switch", 
                "Standard Deviation of processed Bytes to each switch", 

                "Variation of the AVG 1º Packet Delay between (No)Emergency Flows (%)",
                "Variation of the AVG Flow Delay between (No)Emergency Flows (%)"]

num_values_to_compare_all_tests = len(headers_lines)

# Dynamically determine the directory of the script and construct the file path
script_dir = os.path.dirname(os.path.realpath(__file__))
filename_with_sizes = os.path.join(script_dir, "multicast_DSCP.json")
DSCP_IPs = None

All_DSCP = [] # List with all DSCP values sorted

def apply_query(query):
    global client
    try:
        # Execute the query
        result = client.query(query)
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)

    return result

def get_all_sorted_DSCP():
    global All_DSCP, results

    # Cycle through results
    for flow, flow_values in results["1"].items():
        dscp = flow_values["DSCP"]
        if dscp not in All_DSCP:
            All_DSCP.append(dscp)
    
    All_DSCP = sorted(All_DSCP)  