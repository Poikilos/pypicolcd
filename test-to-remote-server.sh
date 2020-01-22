#!/bin/bash
if [ -z "$1" ]; then
    echo "You must specify an IP address or hostname as the parameter."
    exit 1
fi
IP="$1"
PORT=25664
wget http://$IP:$PORT/?json=%7B%22lines%22%3A%20%5B%22hello%22%2C%20%22world%22%5D%7D
