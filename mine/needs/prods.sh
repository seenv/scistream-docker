#!/bin/bash
# Generate a key
openssl genrsa -out server.key 2048

# Create the server.conf file with the required contents
cat <<EOL > server.conf
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = 192.168.100.11

[v3_req]
subjectAltName = IP:192.168.100.11, IP:192.168.100.10, IP:192.168.101.10, IP:192.168.101.11, IP:192.168.102.10, IP:192.168.102.11
EOL

openssl req -new -key server.key -out server.csr -config server.conf
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -extfile server.conf -extensions v3_req

cp server.crt server.key /tmp/

# Print success message
echo "RSA key and server.conf have been created successfully."

# Start scistream's control server
s2cs --verbose --port=5007 --listener-ip=192.168.100.11 --type=Haproxy



