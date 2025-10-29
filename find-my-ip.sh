#!/bin/bash
echo "========================================"
echo "Finding Your Laptop's IP Address"
echo "========================================"
echo ""

# For Windows (Git Bash/MINGW)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "IPv4 Addresses found:"
    ipconfig | grep -i "IPv4" | awk '{print "  ", $NF}'
    echo ""
    echo "========================================"
    echo "Use one of the IP addresses above in your ESP32 firmware:"
    echo "const char* serverUrl = \"http://YOUR_IP:8000/readings\";"
    echo "========================================"
# For Linux/Mac
else
    echo "IP Addresses found:"
    hostname -I 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "  ", $2}'
    echo ""
    echo "========================================"
    echo "Use one of the IP addresses above in your ESP32 firmware:"
    echo "const char* serverUrl = \"http://YOUR_IP:8000/readings\";"
    echo "========================================"
fi

read -p "Press Enter to continue..."
