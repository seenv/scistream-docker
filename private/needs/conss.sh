#!/bin/bash

sleep 15
cp /tmp/server.crt /tmp/server.key ./

sleep 5
s2cs --verbose --port=5007 --listener-ip=192.168.102.10 --type=Haproxy

