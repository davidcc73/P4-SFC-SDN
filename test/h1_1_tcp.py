import socket
import threading

def receive_message(conn):
    while True:
        try:
            data = conn.recv(1024).decode()
            print("\nReceived:", data)
        except Exception as e:
            print("Error receiving message:", e)
            break

def main():
    h2_ip = "2001:1:2::1"  # Change this to h2's IP
    h2_port = 80

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.connect((h2_ip, h2_port))

    print("Connected to h2.")
    print("Type 'exit' to quit.")

    receive_thread = threading.Thread(target=receive_message, args=(s,))
    receive_thread.start()

    while True:
        message = input("Enter message: ")
        if message.lower() == 'exit':
            break
        try:
            s.send(message.encode())
        except Exception as e:
            print("Error sending message:", e)
            break

    s.close()

if __name__ == "__main__":
    main()
