
# Define the directory path
import os
import pprint

from influxdb import InfluxDBClient
import numpy as np


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

script_dir = os.path.dirname(os.path.realpath(__file__))
filename_with_sizes = os.path.join(script_dir, "multicast_DSCP.json")
DSCP_IPs = None

All_DSCP = [] # List with all DSCP values sorted

aux_calculated_results = {}         #auxiliar dictionary to store calculated results before writing in the final file

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

def calulate_std_jitter_per_dscp():
    global aux_calculated_results, results

    aux_calculated_results[-1] = {}                 #initialize the dictionary entry to store the avg_jitters for all DSCP
    aux_calculated_results[-1]["avg_jitters"] = []

    # Group all the avg_jitters by DSCP
    for iteration, iteration_values in results.items():
        for flow, flow_values in iteration_values.items():
            dscp = flow_values["DSCP"]
            current_avg_jitter = flow_values["receiver"]["extra"][2]["avg_jitter"]      #get avg_jitter of current jitter

            if dscp not in aux_calculated_results:
                aux_calculated_results[dscp] = {}
                aux_calculated_results[dscp]["avg_jitters"] = []
            
            aux_calculated_results[-1]["avg_jitters"].append(current_avg_jitter)
            aux_calculated_results[dscp]["avg_jitters"].append(current_avg_jitter)

    # Calculate the std of the avg_jitters
    for dscp, dscp_values in aux_calculated_results.items():
        avg_jitters = dscp_values["avg_jitters"]
        
        # Calculate the std of the avg_jitters, 2 decimal places
        std_jitter = np.std(avg_jitters)
        std_jitter = round(std_jitter, 2)
        aux_calculated_results[dscp]["std_jitter"] = std_jitter