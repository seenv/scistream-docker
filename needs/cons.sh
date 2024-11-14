#!/bin/bash

sleep 20
cp /tmp/server.crt ./

sleep 5
s2uc cons-req --s2cs 192.168.102.10:5007 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.101.10:5074 &

sleep 2
appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.102.10:5007 INVALID_TOKEN PROD 192.168.101.10

tail -f /dev/null