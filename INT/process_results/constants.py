
# Define the directory path
import os
import pprint
import sys
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

index_of_headers_to_do_CDF_out_of_raw_values = [8, 9, 11, 13, 14, 15] # I J L N O P
title_for_each_index_collumn = {        # title to be used for each plot
    8: "1º Packet Delay",
    9: "Nº of out of order packets",
    11: "Flow Jitter",
    13: "Nº of Packets Lost",
    14: "Percentage of Packets Lost",
    15: "1st Packet Delay"
}

units_for_each_index_collumn = {        # units to be used for the x labels of each plot
    8: "Seconds",
    9: "Nº of packets",
    11: "Nanoseconds",
    13: "Nº of packets",
    14: "% of packets",
    15: "Nanoseconds",
}

variables_to_do_CDF_out_of_db_values ={ # variables to do CDF out of DB, key are tables, and values are their variables
    "flow_stats": ["latency"],
    "switch_stats": ["latency"],
}

num_values_to_compare_all_tests = len(headers_lines)

result_directory = "results"
analyzer_directory = "analyzer"
final_file = "final_results.xlsx"
directory_images = "images"
current_directory = os.path.dirname(os.path.abspath(__file__)) 

parent_path = os.path.abspath(os.path.join(current_directory, ".."))
results_path = os.path.join(parent_path, result_directory) 
final_file_path = os.path.join(results_path, final_file) 
images_path = os.path.join(results_path, directory_images)

# Create the directory if it doesn't exist
os.makedirs(images_path, exist_ok=True)
os.makedirs(results_path, exist_ok=True)

args = None
results = {}
percentile = 95             #percentile % to  filter out values, NOT USED EVERYWHERE YET
num_switches = 5           #switches ids go from 1 to 5ss

# Define DB connection parameters
host='localhost'
dbname='int'
# Connect to the InfluxDB client
client = InfluxDBClient(host=host, database=dbname)

algorithms = None
test_scenarios = None

last_line_raw_data = {}              #last line of raw data in each sheet

script_dir = os.path.dirname(os.path.realpath(__file__))
filename_with_sizes = os.path.join(script_dir, "multicast_DSCP.json")
DSCP_IPs = None

DSCP_per_scenario = {               # Dictionary with DSCP values used on each scenario
    "HIGH":[-1, 0, 2, 10, 51]
} 


start_end_times = {} # Dictionary with start and end times for each scenariọ-algorithm pair

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

def get_full_variable_data_from_db(variable, percentile, table, start_time, end_time):
    
    percentile_query = f"""
        SELECT PERCENTILE("{variable}", {percentile}) AS p_latency
        FROM {table}
        WHERE time >= '{start_time}'
        AND time <= '{end_time}'
    """
    percentile_result = apply_query(percentile_query)
    p_latency = list(percentile_result.get_points())[0]['p_latency']

    query = f"""
                SELECT "{variable}"
                FROM {table}
                WHERE time >= '{start_time}'
                AND time <= '{end_time}'
                AND "{variable}" <= {p_latency}
            """
    result = apply_query(query)

    # Extracting just the values, ignoring the timestamps
    full_data = [entry[1] for entry in result.raw["series"][0]["values"]]

    return full_data

def get_collumn_average_per_dscp(sheet, last_line_raw_data_sheet, dscp_collumn_letter, dscp_target, data_collumn_letter, scenario_DSCPs):
    # Get lines from 2 to last_line_raw_data_sheet
    
    values = []
    for i in range(2, last_line_raw_data_sheet + 1):
        # Get the value of the cell
        dscp_value = sheet[f'{dscp_collumn_letter}{i}'].value
        data_value = sheet[f'{data_collumn_letter}{i}'].value

        # Check if the dscp_cell is not empty, and we are not at wrong variable are
        if dscp_value not in scenario_DSCPs or data_value is None:  
            continue

        if dscp_target == dscp_value or dscp_target == -1:                    # -1 means all DSCP
            values.append(data_value)   

    if len(values) == 0:
        print(f"Warning: No values found for DSCP {dscp_target} in column {data_collumn_letter}, sheet.title: {sheet.title}")
        sys.exit(1)
        
    # Apply percentile
    percentile_values = np.percentile(values, percentile)

    # Filter the values with the percentile value
    values = np.array(values)
    values = values[values <= percentile_values]
    
    # Calculate the average
    return round(np.mean(values), 2)

def calulate_std_jitter_per_dscp(current_filename):
    global aux_calculated_results, results, percentile
    scenario_algorithms = current_filename.split("_")[0]

    aux_calculated_results[scenario_algorithms] = {}
    aux_calculated_results[scenario_algorithms][-1] = {}                 #initialize the dictionary entry to store the avg_jitters for all DSCP
    aux_calculated_results[scenario_algorithms][-1]["avg_jitters"] = []

    # Group all the avg_jitters by DSCP
    for iteration, iteration_values in results.items():
        for flow, flow_values in iteration_values.items():
            if flow == "SRv6_Operations":                                #skip the SRv6_Operations data for the current iteration
                continue
            dscp = flow_values["DSCP"]
            current_avg_jitter = flow_values["receiver"]["extra"]["avg_jitter"]      #get avg_jitter of current jitter

            if dscp not in aux_calculated_results[scenario_algorithms]:
                aux_calculated_results[scenario_algorithms][dscp] = {}
                aux_calculated_results[scenario_algorithms][dscp]["avg_jitters"] = []
            
            aux_calculated_results[scenario_algorithms][-1]["avg_jitters"].append(current_avg_jitter)
            aux_calculated_results[scenario_algorithms][dscp]["avg_jitters"].append(current_avg_jitter)

    # Calculate the std of the avg_jitters
    for dscp, dscp_values in aux_calculated_results[scenario_algorithms].items():
        avg_jitters = dscp_values["avg_jitters"]
        
        # Calculate the std of the avg_jitters, 2 decimal places, and applying a percentile
        avg_jitters = np.array(avg_jitters)
        avg_jitters_percentile_value = np.percentile(avg_jitters, percentile)
        
        # Filter the avg_jitters with the percentile value
        avg_jitters_filtered = avg_jitters[avg_jitters <= avg_jitters_percentile_value]
        if len(avg_jitters_filtered) > 2:              #Only apply percentile if we have more than 2 values
            avg_jitters = avg_jitters_filtered

        std_jitter = round(np.std(avg_jitters), 2)
        aux_calculated_results[scenario_algorithms][dscp]["std_jitter"] = std_jitter
