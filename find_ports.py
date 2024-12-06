import socket

def find_ports(start_port=1, end_port=65535):
    free_ports = []
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                free_ports.append(port)
            except OSError:
                continue
    return free_ports

if __name__ == "__main__":
    start = 1024 
    end = 65535
    print(f"finding available ports from {start} to {end}...")
    free_ports = find_ports(start, end)
    print(f"Available ports: {free_ports}")
