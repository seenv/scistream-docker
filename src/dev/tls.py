import socket
import ssl

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8443))
server_socket.listen(1)

# Define the PSK and identity
psk = b'my_secret_key'
psk_identity = b'my_identity'

def psk_callback(identity, context):
    if identity == psk_identity:
        return psk
    else:
        return None

# Wrap the socket with TLS
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.set_ciphers('TLS_PSK_WITH_NULL_SHA256')
context.set_psk_server_callback(psk_callback)

# Accept client connection
client_socket, address = server_socket.accept()
ssl_client_socket = context.wrap_socket(client_socket, server_side=True)

# Receive data from the client
data = ssl_client_socket.recv(1024)
print(f'Received: {data.decode()}')

# Send a response back to the client
ssl_client_socket.sendall(b'Hello, client!')

# Close the TLS connection and the server socket
ssl_client_socket.close()
server_socket.close()


import socket
import ssl

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the PSK and identity
psk = b'my_secret_key'
psk_identity = b'my_identity'

# Wrap the socket with TLS
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.set_ciphers('TLS_PSK_WITH_NULL_SHA256')
context.set_psk_client_callback(lambda hint: (psk_identity, psk))

# Connect to the server
server_address = ('localhost', 8443)
ssl_sock = context.wrap_socket(sock)
ssl_sock.connect(server_address)

# Send data to the server
ssl_sock.sendall(b'Hello, server!')

# Receive a response from the server
data = ssl_sock.recv(1024)
print(f'Received: {data.decode()}')

# Close the TLS connection
ssl_sock.close()
