#!/bin/bash

sleep 5
cp /tmp/server.crt ./

sleep 5
s2uc prod-req --s2cs 192.168.100.11:5007 --mock True &

sleep 5
appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 192.168.100.11:5007 INVALID_TOKEN PROD 192.168.100.10

tail -f /dev/null