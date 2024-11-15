# Docker Compose implementation of the SciStream


- Just make sure you have the Docker on the system
- Run `docker-compose up --build`


Commands Order on each Container:
    1. p2cs (scistream control server on producer side):
        - Generating a private key
            - `openssl genrsa -out server.key 2048`
        - Creating the server.conf to add the IPs of each container
            - ```
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
            ```
        - Generate a Certificate Signing Request (CSR)
            - `openssl req -new -key server.key -out server.csr -config server.conf`
        - Creating a Self-Signed Certificate
            - `openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -extfile server.conf -extensions v3_req`
        - Moving the files to `/tmp` so they can be accessable for others
            - `cp server.crt server.key /tmp/`
        - Starting scistream's control server
            - `s2cs --verbose --port=5007 --listener-ip=192.168.100.11 --type=Haproxy`
    2. producre:
        - Copying the certificate:
            - `cp /tmp/server.crt ./`
        - Specifying the stream endpoint details:
            - `s2uc prod-req --s2cs 192.168.100.11:5007 --mock True &`
        - Starting the application controller mock:
            - `appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.100.11:5007 INVALID_TOKEN PROD 192.168.100.10`
