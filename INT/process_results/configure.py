from cmath import sqrt
import constants
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font



def get_line_column_to_copy_from(sheet_to_copy_from_name, variable_number):
    line =None
    col = None

    workbook = load_workbook(constants.final_file_path)
    sheet_to_copy_from = workbook[sheet_to_copy_from_name]

    variable_name = constants.headers_lines[variable_number]

    pass_1_occurance = True          #there are 2 Lines on collumn A that have the same name
    if variable_number == 12:
        pass_1_occurance = False 

    # sheet_to_copy_from, get the line of the cell that contains the variable_name on collumn A and the collumn after it
    for row in sheet_to_copy_from.iter_rows(min_row=1, max_row=sheet_to_copy_from.max_row, min_col=1, max_col=1):
        
        if pass_1_occurance == False and row[0].value == "AVG 1º Packet Delay (nanoseconds)":
            pass_1_occurance = True
            continue
        
        if variable_number <= 7:
            if row[0].value == variable_name:
                # Get the next collumn letter of the cell that contains the variable_name
                line = row[0].row
                col = get_column_letter(row[0].column + 1)
                break
        elif variable_number == 8 or variable_number == 10:
            if row[0].value == "Mean":
                line = row[0].row
                if variable_number == 8:
                    col = get_column_letter(row[0].column + 1)
                else:
                    col = get_column_letter(row[0].column + 2)
                break
        elif variable_number == 9 or variable_number == 11:
            if row[0].value == "Standard Deviation":
                line = row[0].row
                if variable_number == 9:
                    col = get_column_letter(row[0].column + 1)
                else:
                    col = get_column_letter(row[0].column + 2)
                break
        elif variable_number == 12:
            if row[0].value == "AVG 1º Packet Delay (nanoseconds)":
                line = row[0].row
                col = get_column_letter(row[0].column + 3)
                break
        elif variable_number == 13:
            if row[0].value == "AVG Flow Delay (nanoseconds)":
                line = row[0].row
                col = get_column_letter(row[0].column + 3)
                break

    return line, col

def get_byte_sum(start, end):
    # Initialize the result dictionary to store total byte counts per switch ID
    sum = {}
    switch_ids = []

    #--------------Query to get unique switch_id values if it is a tag
    # This approche did not take into account the existing but unused switches
    #query = f'''
    #        SHOW TAG VALUES 
    #        FROM "switch_stats"  
    #        WITH KEY = "switch_id"
    #        WHERE time >= '{start}' AND time <= '{end}' 
    #    '''
    #tmp = constants.apply_query(query)  

    # Extract the switch_id values into a list
    #for row in tmp.raw["series"][0]["values"]:
    #    switch_ids.append(int(row[1]))

    switch_ids = list(range(1, constants.num_switches + 1))

    #pprint(switch_ids)

    # Loop through each unique switch ID
    for switch_id in switch_ids:
        # Formulate the query to get the sum of bytes for the given switch ID and time range
        query = f"""
            SELECT SUM("size") AS total_count
            FROM flow_stats 
            WHERE time >= '{start}' AND time <= '{end}' 
            AND path =~ /(^|-)({switch_id})(-|$|\b)/
        """

        result = constants.apply_query(query)  # Assume this returns a dictionary with 'total_count'
        
        # Add the result to the sum dictionary under the switch_id key
        #print(f"Switch ID: {switch_id}")
        #print(result.raw)
        sum[switch_id] = {}
        if not result.raw["series"]:
            sum[switch_id]["Byte Sums"] = 0
        else:
            sum[switch_id]["Byte Sums"] = result.raw["series"][0]["values"][0][1]
    #pprint(sum)

    return sum

def calculate_percentages(start, end, switch_data):
    # Get the total count of packets
    query = f"""
        SELECT COUNT("latency") AS total_count
        FROM flow_stats
        WHERE time >= '{start}' AND time <= '{end}'
    """
    result = constants.apply_query(query)
    total_count = result.raw["series"][0]["values"][0][1]  # Extract total_count from the result

    # Get the count of packets that went to each switch
    query = f"""
        SELECT COUNT("latency") AS switch_count
        FROM switch_stats
        WHERE time >= '{start}' AND time <= '{end}'
        GROUP BY switch_id
    """
    result = constants.apply_query(query)
    
    # Calculate the percentage of packets that went to each switch
    # initialize to all switches as 0, so unused switches are takrn into account too
    for switch_id in range(1, constants.num_switches + 1):
        switch_data[switch_id]["Percentage Pkt"] = 0

    for row in result.raw["series"]:
        #tuple pair: id, count
        switch_id = int(row["tags"]["switch_id"])
        switch_count = int(row["values"][0][1])
        switch_data[switch_id]["Percentage Pkt"] = round((switch_count / total_count) * 100, 3)

    #pprint(switch_data)
    return switch_data

def get_mean_standard_deviation(switch_data):
    #pprint(switch_data)
    sum_percentage = 0
    sum_byte = 0
    count = 0

    # Get the mean of the (Byte Sums) and (Percentage Pkt) for all switches in switch_data
    for switch_id in switch_data:
        sum_percentage += switch_data[switch_id]["Percentage Pkt"]
        sum_byte += switch_data[switch_id]["Byte Sums"]
        count += 1

    percentage_mean = sum_percentage / count
    byte_mean = sum_byte / count
    

    # Get the Standard Deviation of the (Byte Sums) and (Percentage Pkt) for all switches in switch_data
    sum_squared_diff_percentage = 0
    sum_squared_diff_byte = 0
    
    for switch_id in switch_data:
        current_percentage = switch_data[switch_id]["Percentage Pkt"]
        current_byte = switch_data[switch_id]["Byte Sums"]
        sum_squared_diff_percentage += (current_percentage - percentage_mean) ** 2
        sum_squared_diff_byte += (current_byte - byte_mean) ** 2
    
    percentage_std_dev = sqrt(sum_squared_diff_percentage / count).real
    byte_std_dev = sqrt(sum_squared_diff_byte / count).real

    #print("percentage_std_dev: ", percentage_std_dev)
    #print("byte_std_dev: ", percentage_std_dev)
    
    switch_data["Percentage Mean"] = round(percentage_mean, 3)
    switch_data["Byte Mean"] = round(byte_mean, 3)
    switch_data["Percentage Standard Deviation"] = round(percentage_std_dev, 3)
    switch_data["Byte Standard Deviation"] = round(byte_std_dev, 3)

    return switch_data

def write_INT_results(file_path, workbook, sheet, AVG_flows_latency, STD_flows_latency, AVG_hop_latency, STD_hop_latency, switch_data):
    # Write the results in the sheet
    last_line = sheet.max_row + 1

    # Set new headers
    sheet[f'A{last_line + 0}'] = "AVG Flows Latency (nanoseconds)"
    sheet[f'A{last_line + 1}'] = "STD Flows Latency (nanoseconds)"
    sheet[f'A{last_line + 2}'] = "AVG Hop Latency (nanoseconds)"
    sheet[f'A{last_line + 3}'] = "STD Hop Latency (nanoseconds)"

    sheet[f'A{last_line + 0}'].font = Font(bold=True)
    sheet[f'A{last_line + 1}'].font = Font(bold=True)
    sheet[f'A{last_line + 2}'].font = Font(bold=True)
    sheet[f'A{last_line + 3}'].font = Font(bold=True)

    sheet[f'B{last_line + 0}'] = AVG_flows_latency
    sheet[f'B{last_line + 1}'] = STD_flows_latency
    sheet[f'B{last_line + 2}'] = AVG_hop_latency
    sheet[f'B{last_line + 3}'] = STD_hop_latency


    sheet[f'A{last_line + 5}'] = "Switch ID"
    sheet[f'B{last_line + 5}'] = "% of packets to each switch"
    sheet[f'C{last_line + 5}'] = "Total Sum of Processed Bytes"

    sheet[f'A{last_line + 5}'].font = Font(bold=True)
    sheet[f'B{last_line + 5}'].font = Font(bold=True)
    sheet[f'C{last_line + 5}'].font = Font(bold=True)


    # Write percentages and total bytes processed, cycle through keys that are numbers
    #pprint(switch_data)
    #print("----------------------------------------")
    for i, key in enumerate(switch_data.keys()):
        if isinstance(key, int):                #skip sets that are non-switch_id
            #print(f"Key: {key} is an integer")
            #print(f"i: {i}, Switch ID: {key},  Values: {switch_data[key]}")
            sheet[f'A{last_line + 6 + i}'] = key
            
            #percentage of total packets that went to each switch
            sheet[f'B{last_line + 6 + i}'] = switch_data[key]["Percentage Pkt"]
            
            #Sum of processed bytes
            sheet[f'C{last_line + 6 + i}'] = switch_data[key]["Byte Sums"]

    # Write the mean and standard deviation of the percentages and bytes
    
    sheet[f'A{last_line + constants.num_switches + 5 + 1}'] = "Mean"
    sheet[f'A{last_line + constants.num_switches + 5 + 2}'] = "Standard Deviation"
    sheet[f'A{last_line + constants.num_switches + 5 + 1}'].font = Font(bold=True)
    sheet[f'A{last_line + constants.num_switches + 5 + 2}'].font = Font(bold=True)

    sheet[f'B{last_line + constants.num_switches + 5 + 1}'] = switch_data["Percentage Mean"]
    sheet[f'B{last_line + constants.num_switches + 5 + 2}'] = switch_data["Percentage Standard Deviation"]
    sheet[f'C{last_line + constants.num_switches + 5 + 1}'] = switch_data["Byte Mean"]
    sheet[f'C{last_line + constants.num_switches + 5 + 2}'] = switch_data["Byte Standard Deviation"]
    

    # Save the workbook
    workbook.save(file_path)


def set_pkt_loss():

    # Configure each sheet
    workbook = load_workbook(constants.final_file_path)

    # Set formula for each sheet
    for sheet in workbook.sheetnames:
        sheet = workbook[sheet]

        #Set new headers
        sheet['M1'] = "Packet Loss"
        sheet['N1'] = "Packet Loss (%)"

        sheet['M1'].font = Font(bold=True)
        sheet['N1'].font = Font(bold=True)

        no_formula_section = False

        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=3):
            if row[0].value == "Calculations":
                break

            if row[0].value and row[0].value.startswith("Iteration -"):
                no_formula_section = False
            if no_formula_section:
                continue

            #if cell from collumn A does not contain an IPv4 address, skip
            if row[0].value is None or "." not in row[0].value:
                skip = True
                continue
            if skip:            #not in the right line of the pair
                skip = False
                continue
            
            # Set the formula, pkt loss, -1 is sender, 0 is receiver
            sheet[f'M{row[0].row}'] = f'=H{row[0].row-1}-H{row[0].row}'     
            sheet[f'N{row[0].row}'] = f'=ROUND((M{row[0].row}/H{row[0].row-1})*100, 3)'

            skip = True

    # Save the workbook
    workbook.save(constants.final_file_path)

def set_fist_pkt_delay():

    # Configure each sheet
    workbook = load_workbook(constants.final_file_path)
    
    # Set formula for each sheet
    for sheet in workbook.sheetnames:
        sheet = workbook[sheet]

        #Set new headers as bold text
        sheet['O1'] = "1º Packet Delay (nanoseconds)"
        sheet['O1'].font = Font(bold=True)

        no_formula_section = False
        
        # Set collumn L to contain a formula to be the subtraction of values of collum F of the current pair of lines
        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=3):
            if row[0].value == "Calculations":
                break

            if row[0].value and row[0].value.startswith("Iteration -"):
                no_formula_section = False
            if no_formula_section:
                continue

            #if cell from collumn A does not contain an IPv4 address, skip
            if row[0].value is None or "." not in row[0].value:
                skip = True
                continue
            if skip:            #not in the right line of the pair
                skip = False
                continue
            #print(row)
            
            # Set the formula, pkt loss, -1 is sender, 0 is receiver
            # The values are 2 Timestamp (seconds-Unix Epoch)
            # subtraction give seconds, we convert to nanoseconds
            sheet[f'O{row[0].row}'] = f'=ROUND((I{row[0].row}-I{row[0].row-1})*10^9, 3)'     

            skip = True

    # Save the workbook
    workbook.save(constants.final_file_path)

def set_caculations():
    # Configure each sheet
    workbook = load_workbook(constants.final_file_path)

    # Set formula for each sheet
    for sheet in workbook.sheetnames:
        sheet = workbook[sheet]

        #Pass the last line with data, and leave 2 empty lines
        last_line = sheet.max_row + 4

        #Set new headers
        sheet[f'A{last_line}'] = "Calculations"
        sheet[f'A{last_line + 1}'] = "AVG Out of Order Packets (Nº)"
        sheet[f'A{last_line + 2}'] = "AVG Packet Loss (Nº)"
        sheet[f'A{last_line + 3}'] = "AVG Packet Loss (%)"
        sheet[f'A{last_line + 4}'] = "AVG 1º Packet Delay (nanoseconds)"
        sheet[f'B{last_line}'] = "Values"

        sheet[f'A{last_line}'].font = Font(bold=True)
        sheet[f'A{last_line + 1}'].font = Font(bold=True)
        sheet[f'A{last_line + 2}'].font = Font(bold=True)
        sheet[f'A{last_line + 3}'].font = Font(bold=True)
        sheet[f'A{last_line + 4}'].font = Font(bold=True)
        sheet[f'B{last_line}'].font = Font(bold=True)

        # on the next line for each column, set the average of the column, ignore empty cells
        sheet[f'B{last_line + 1}'] = f'=ROUND(AVERAGEIF(J:J, "<>", J:J), 3)'
        sheet[f'B{last_line + 2}'] = f'=ROUND(AVERAGEIF(M:M, "<>", M:M), 3)'
        sheet[f'B{last_line + 3}'] = f'=ROUND(AVERAGEIF(N:N, "<>", N:N), 3)'
        sheet[f'B{last_line + 4}'] = f'=ROUND(AVERAGEIF(O:O, "<>", O:O), 3)'



    # Save the workbook
    workbook.save(constants.final_file_path)

def set_INT_results():
    # For each sheet and respectice file, see the time interval given, get the values from the DB, and set the values in the sheet
        
    # Configure each sheet
    workbook = load_workbook(constants.final_file_path)

    # Get nº each sheet
    for i, sheet in enumerate(workbook.sheetnames):

        #can i can not exceed the number of args.f (last one is comparasions)
        if i >= len(constants.args.f):
            break

        print(f"Processing sheet {sheet}, index {i}")
        sheet = workbook[sheet]

        # Get the start and end times
        start = constants.args.start[i]
        end = constants.args.end[i]

        ############################################ Get the results from the DB
        # We need AVG Latency of ALL flows combined (NOT distinguishing between flows)
        # Query to get the 95th percentile latency value, to exclude outliers
        percentile_query = f"""
            SELECT PERCENTILE("latency", 95) AS p_latency
            FROM flow_stats
            WHERE time >= '{start}' AND time <= '{end}'
        """

        percentile_result = constants.apply_query(percentile_query)
        p_latency = list(percentile_result.get_points())[0]['p_latency']   #nanoseconds

        query = f"""
                    SELECT MEAN("latency"), STDDEV("latency")
                    FROM  flow_stats
                    WHERE time >= '{start}' AND time <= '{end}' AND "latency" <= {p_latency}
                """
        result = constants.apply_query(query)
        AVG_flows_latency = round(result.raw["series"][0]["values"][0][1], 3)         #nanoseconds
        STD_flows_latency = round(result.raw["series"][0]["values"][0][2], 3)

        ###########################################
        # We need AVG Latency for processing of ALL packets (NOT distinguishing between switches/flows) 
        # Query to get the 95th percentile latency value, to exclude outliers
        percentile_query = f"""
            SELECT PERCENTILE("latency", 95) AS p_latency
            FROM switch_stats
            WHERE time >= '{start}' AND time <= '{end}'
        """
        
        query = f"""
                    SELECT MEAN("latency"), STDDEV("latency")
                    FROM  switch_stats
                    WHERE time >= '{start}' AND time <= '{end}' AND "latency" <= {p_latency}
                """
        result = constants.apply_query(query)
        AVG_hop_latency = round(result.raw["series"][0]["values"][0][1], 3)         #nanoseconds
        STD_hop_latency = round(result.raw["series"][0]["values"][0][2], 3)         

        # % of packets that went to each individual switch (switch_id)
        switch_data = get_byte_sum(start, end)
        switch_data = calculate_percentages(start, end, switch_data)
        switch_data = get_mean_standard_deviation(switch_data)

        #pprint("AVG_flows_latency: ", AVG_flows_latency)
        #pprint("AVG_hop_latency: ", AVG_hop_latency)
        #pprint("switch_data: ", switch_data)

        write_INT_results(constants.final_file_path, workbook, sheet, AVG_flows_latency, STD_flows_latency, AVG_hop_latency, STD_hop_latency, switch_data)

def get_flow_delays(start, end):
    # Get the average delay of emergency and non-emergency flows
    query = f"""
        SELECT MEAN("latency") 
        FROM  flow_stats WHERE time >= '{start}' 
        AND time <= '{end}' 
        AND dscp >= 40
    """
    result = constants.apply_query(query)
    if not result.raw["series"]:
        avg_emergency_flows_delay = "none"
    else:
        avg_emergency_flows_delay = round(result.raw["series"][0]["values"][0][1], 3)         #nanoseconds

    query = f"""
        SELECT MEAN("latency")
        FROM  flow_stats
        WHERE time >= '{start}' AND time <= '{end}'
        AND dscp < 40
    """

    result = constants.apply_query(query)
    if not result.raw["series"]:
        avg_non_emergency_flows_delay = "none"
    else:
        avg_non_emergency_flows_delay = round(result.raw["series"][0]["values"][0][1], 3)         #nanoseconds

    return avg_emergency_flows_delay, avg_non_emergency_flows_delay 

def set_Emergency_calculation():
    # Configure each sheet
    workbook = load_workbook(constants.final_file_path)

    for i, sheet in enumerate(workbook.sheetnames):
        #can i can not exceed the number of args.f (last one is comparasions)
        if i >= len(constants.args.f):
            break

        sheet = workbook[sheet]

        # Set new headers
        max_line = sheet.max_row
        sheet[f'A{max_line + 2}'] = "Flows Types"
        sheet[f'B{max_line + 2}'] = "Non-Emergency Flows"
        sheet[f'C{max_line + 2}'] = "Emergency Flows"
        sheet[f'D{max_line + 2}'] = "Variation (%)"
        
        sheet[f'A{max_line + 3}'] = "AVG 1º Packet Delay (nanoseconds)"
        sheet[f'A{max_line + 4}'] = "AVG Flow Delay (nanoseconds)"

        sheet[f'A{max_line + 2}'].font = Font(bold=True)
        sheet[f'B{max_line + 2}'].font = Font(bold=True)
        sheet[f'C{max_line + 2}'].font = Font(bold=True)
        sheet[f'D{max_line + 2}'].font = Font(bold=True)
        sheet[f'A{max_line + 3}'].font = Font(bold=True)
        sheet[f'A{max_line + 4}'].font = Font(bold=True)

        #print(f"Processing sheet {sheet}")
        #print(f"arg.f: {constants.args.f}")
        #get the index of the constants.args.f which the name starts with the current sheet name
        #print(f"Index: {i}")
        start = constants.args.start[i]
        end = constants.args.end[i]

        avg_emergency_flows_delay, avg_non_emergency_flows_delay = get_flow_delays(start, end)

        # Define the row range to consider
        row_range = max_line - 1  # Rows before the max line

        # Set the formula for the Non-Emergency Flows
        sheet[f'B{max_line + 3}'] = f'=SUMIF(E1:E{row_range}, "<40" , O1:O{row_range})'  
        sheet[f'B{max_line + 4}'] = avg_non_emergency_flows_delay

        # Set the formula for the Emergency Flows
        sheet[f'C{max_line + 3}'] = f'=SUMIF(E1:E{row_range}, ">=40", O1:O{row_range})'
        sheet[f'C{max_line + 4}'] = avg_emergency_flows_delay

        #Set comparasion formulas, for the AVG 1º Packet Delay and AVG Flow Delay in percentage
        sheet[f'D{max_line + 3}'] = f'=IFERROR(ROUND((C{max_line + 3} - B{max_line + 3})/ABS(B{max_line + 3}) * 100, 3), "none")'
        sheet[f'D{max_line + 4}'] = f'=IFERROR(ROUND((C{max_line + 4} - B{max_line + 4})/ABS(B{max_line + 4}) * 100, 3), "none")'


    workbook.save(constants.final_file_path)

def set_copied_values(sheet, test_case, start_line):    
    print("Seting values copy from other sheets")
    
    # Cycle through the variables to compare (lines)
    for variable_number in range(constants.num_values_to_compare_all_tests):
        
        # Cycle through the args.f to copy the values (columns)
        for i in range(len(constants.args.f)):
            
            #--------------Collumn C is the second algorithm
            #parse 1st element pre _ in args.f
            sheet_to_copy_from_name = constants.args.f[i].split("_")[0]
            line, column = get_line_column_to_copy_from(sheet_to_copy_from_name, variable_number)

            if line is None or column is None:
                print(f"Error getting line and column to copy from, sheet_to_copy_from: {sheet_to_copy_from_name}, variable number: {variable_number}")
                continue

            cell_reference = f"{column}{line}"
            formula = f"='{sheet_to_copy_from_name}'!{cell_reference}"
            sheet[f'{get_column_letter(2 + i)}{start_line + variable_number + 1}'] = formula

def set_Comparison_sheet():
    print("Setting the Comparison sheet")

    # Create the comparison sheet
    workbook = load_workbook(constants.final_file_path)
    sheet = workbook.create_sheet(title="Comparison")

    title = "Load Test Cases"
    sheet[f'A1'] = title
    sheet[f'A1'].font = Font(bold=True)

    sheet[f'A2'] = f"Variation: From {constants.algorithms[0]} to {constants.algorithms[1]}"

    # Empty line
    sheet.append([""])
    
    # Create a block for each test case
    for test_case in constants.test_cases:
        # Get max line considering the previous test cases
        max_line = sheet.max_row + 1

        set_algorithm_headers(sheet, test_case, max_line)
        set_comparasion_formulas(sheet, max_line)
        set_copied_values(sheet, test_case, max_line)

        # Insert 2 empty lines
        sheet.append([""])
        sheet.append([""])

    # Save the workbook
    workbook.save(constants.final_file_path)


def configure_final_file():
    set_pkt_loss()
    set_fist_pkt_delay()
    set_caculations()
    set_INT_results()
    set_Emergency_calculation()
    set_Comparison_sheet()



def set_algorithm_headers(sheet, test_case, start_line):

    # Set test case name in bold test
    title = f"{test_case}"
    sheet[f'A{start_line}'] = title
    sheet[f'A{start_line}'].font = Font(bold=True)

    # Set the collumn names
    sheet[f'B{start_line}'] = constants.algorithms[0]
    sheet[f'C{start_line}'] = constants.algorithms[1]
    sheet[f'D{start_line}'] = "Variation (%)"

    # Set collumn names in bold text
    sheet[f'B{start_line}'].font = Font(bold=True)
    sheet[f'C{start_line}'].font = Font(bold=True)
    sheet[f'D{start_line}'].font = Font(bold=True)

    # Set the lines names
    sheet[f'A{start_line + 1}'] = constants.headers_lines[0]
    sheet[f'A{start_line + 2}'] = constants.headers_lines[1]
    sheet[f'A{start_line + 3}'] = constants.headers_lines[2]
    sheet[f'A{start_line + 4}'] = constants.headers_lines[3]
    sheet[f'A{start_line + 5}'] = constants.headers_lines[4]
    sheet[f'A{start_line + 6}'] = constants.headers_lines[5]
    sheet[f'A{start_line + 7}'] = constants.headers_lines[6]
    sheet[f'A{start_line + 8}'] = constants.headers_lines[7]
    sheet[f'A{start_line + 9}'] = constants.headers_lines[8]
    sheet[f'A{start_line + 10}'] = constants.headers_lines[9]
    sheet[f'A{start_line + 11}'] = constants.headers_lines[10]
    sheet[f'A{start_line + 12}'] = constants.headers_lines[11]
    sheet[f'A{start_line + 13}'] = constants.headers_lines[12]
    sheet[f'A{start_line + 14}'] = constants.headers_lines[13]


    # Set lines names in bold text
    sheet[f'A{start_line + 1}'].font = Font(bold=True)
    sheet[f'A{start_line + 2}'].font = Font(bold=True)
    sheet[f'A{start_line + 3}'].font = Font(bold=True)
    sheet[f'A{start_line + 4}'].font = Font(bold=True)
    sheet[f'A{start_line + 5}'].font = Font(bold=True)
    sheet[f'A{start_line + 6}'].font = Font(bold=True)
    sheet[f'A{start_line + 7}'].font = Font(bold=True)
    sheet[f'A{start_line + 8}'].font = Font(bold=True)
    sheet[f'A{start_line + 9}'].font = Font(bold=True)
    sheet[f'A{start_line + 10}'].font = Font(bold=True)
    sheet[f'A{start_line + 11}'].font = Font(bold=True)
    sheet[f'A{start_line + 12}'].font = Font(bold=True)
    sheet[f'A{start_line + 13}'].font = Font(bold=True)
    sheet[f'A{start_line + 14}'].font = Font(bold=True)

def set_comparasion_formulas(sheet, start_line):
    # Set the formulas to compare the results between the test cases
    for i in range(1, constants.num_values_to_compare_all_tests + 1):
        #print(sheet[f'A{start_line + i}'].value)
        sheet[f'D{start_line + i}'] = f'=IFERROR(ROUND((C{start_line + i} - B{start_line + i}) / ABS(B{start_line + i}) * 100, 2), 0)'
