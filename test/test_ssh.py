import paramiko
import time

def connect_to_onos():
    # Define connection parameters
    hostname = 'localhost'
    port = 8101
    username = 'onos'
    password = 'rocks' 

    # Create an SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the ONOS CLI
        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False
        )
        
        # Open a session
        session = client.invoke_shell()
        
        # Allow some time for the session to be ready
        time.sleep(1)
        
        # Check if the channel is active
        if session.recv_ready():
            print(session.recv(1024).decode('utf-8'))
        
        return session

    except Exception as e:
        print(f"Failed to connect: {e}")
        client.close()
        return None

def send_command(session, command):
    if session:
        session.send(command + '\n')
        time.sleep(1)  # Wait for the command to be executed

        output = ""
        while session.recv_ready():
            output += session.recv(1024).decode('utf-8')
        return output
    else:
        return "Session not established"

def print_menu():
    menu = """
    ONOS CLI Command Menu:
    1. Push KShort Paths
    2. Push ECMP Paths
    3. Create SRv6 Rule
    4. Remove SRv6 Rule
    0. Quit
    """
    print(menu)

def get_command(choice):
    commands = {
        '1': 'Calculate-Routing-Paths KShort',
        '2': 'Calculate-Routing-Paths ECMP',
        '3': 'srv6-insert device:r%d %s %s %d %d %d %d %s',
        '4': 'srv6-remove device:r%d %s %s %d %d %d %d'
    }
    return commands.get(choice, None)

def form_srv6(command, choice):
    device_id = 1

    src_ip = "2001:1:1::1"
    src_mask = 128

    dst_ip = "2001:1:2::1"
    dst_mask = 128

    flow_label = 2
    flow_label_mask = 255

    if choice == '3':
        sid_list = 'fcbb:bb00:8:7:2:fd00::'
        command = command % (device_id, src_ip, dst_ip, flow_label, src_mask, dst_mask, flow_label_mask, sid_list)
    elif choice == '4':
        command = command % (device_id, src_ip, dst_ip, flow_label, src_mask, dst_mask, flow_label_mask)

    print(f"Command: {command}")
    return command

if __name__ == "__main__":
    session = connect_to_onos()
    
    if session:
        while True:
            print_menu()
            choice = input("Enter your choice: ")
            if choice == '0':
                break
            
            command = get_command(choice)
            if command:
                if choice == '3' or choice == '4': command = form_srv6(command, choice)
                output = send_command(session, command)
                print(output)
            else:
                print("Invalid choice. Please try again.")
        
        session.close()
    else:
        print("Could not establish connection to ONOS CLI")
