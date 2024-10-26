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
    h1_ip = "::1"  # Change this to h1's IP
    h1_port = 80

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.bind((h1_ip, h1_port))
    s.listen(1)

    print("Listening for connection from h1...")

    conn, addr = s.accept()
    print("Connected to h1.")

    receive_thread = threading.Thread(target=receive_message, args=(conn,))
    receive_thread.start()

    while True:
        message = input("Enter message: ")
        if message.lower() == 'exit':
            break
        try:
            conn.send(message.encode())
        except Exception as e:
            print("Error sending message:", e)
            break

    conn.close()
    s.close()

if __name__ == "__main__":
    main()
