# Docker Compose Implementation of the SciStream

This repository contains the Docker Compose configuration for running SciStream.

## Prerequisites
- Ensure Docker is installed on your system.
- Run the following command to start the setup:

```bash
docker-compose up --build
```

## Commands to Run in Each Container

### 1. `p2cs` (SciStream Control Server on the Producer Side)
1. **Generate a private key:**
   ```bash
   openssl genrsa -out server.key 2048
   ```

2. **Create the `server.conf` file to define IPs for each container:**
   ```bash
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

3. **Generate a Certificate Signing Request (CSR):**
   ```bash
   openssl req -new -key server.key -out server.csr -config server.conf
   ```

4. **Create a self-signed certificate:**
   ```bash
   openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -extfile server.conf -extensions v3_req
   ```

5. **Move the certificate files to `/tmp` for accessibility:**
   ```bash
   cp server.crt server.key /tmp/
   ```

6. **Start SciStream's control server:**
   ```bash
   s2cs --verbose --port=5007 --listener-ip=192.168.100.11 --type=Haproxy
   ```

---

### 2. `producer` Container
1. **Copy the certificate from `/tmp`:**
   ```bash
   cp /tmp/server.crt ./
   ```

2. **Specify the stream endpoint details:**
   ```bash
   s2uc prod-req --s2cs 192.168.100.11:5007 --mock True &
   ```

3. **Start the application controller mock:**
   ```bash
   appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.100.11:5007 INVALID_TOKEN PROD 192.168.100.10
   ```

---

### 3. `c2cs` Container
1. **Copy the certificate from `/tmp`:**
   ```bash
   cp /tmp/server.crt ./
   ```

2. **Specify the stream endpoint details:**
   ```bash
   s2uc cons-req --s2cs 192.168.101.11:5007 --mock True &
   ```

3. **Start the application controller mock:**
   ```bash
   appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.101.11:5007 INVALID_TOKEN CONS 192.168.101.10
   ```

---

### 4. `consumer` Container
1. **Copy the certificate from `/tmp`:**
   ```bash
   cp /tmp/server.crt ./
   ```

2. **Specify the stream endpoint details:**
   ```bash
   s2uc cons-req --s2cs 192.168.102.11:5007 --mock True &
   ```

3. **Start the application controller mock:**
   ```bash
   appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.102.11:5007 INVALID_TOKEN CONS 192.168.102.10
   ```

---

## Networks
The following networks are defined in the `docker-compose.yml` file:

- **Producer Network**: Subnet `192.168.100.0/24`
- **S2CS Network**: Subnet `192.168.101.0/24`
- **Consumer Network**: Subnet `192.168.102.0/24`

Ensure that your Docker environment supports these network configurations.

---
