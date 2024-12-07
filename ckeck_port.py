import socket

def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Try connecting to the port
        result = sock.connect_ex((ip, port))
        if result == 0:
            print(f"Port {port} on {ip} is not available")
        else:
            print(f"Port {port} on {ip} is available")


