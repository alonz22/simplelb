#!/bin/bash

# Create the folder 'simplelb' inside /etc
sudo mkdir -p /etc/simplelb

# Copy 'config.ini' to the 'simplelb' folder
sudo cp config.ini /etc/simplelb/

# Copy 'loadbalancer.py' to /usr/bin
sudo cp loadbalancer.py /usr/bin/


# Create the service file for 'simplelb' (Assuming you want a systemd service)
cat << EOF | sudo tee /etc/systemd/system/simplelb.service
[Unit]
Description=Simple Load Balancer Service By Alon Zur

[Service]
ExecStart=/usr/bin/python3 /usr/bin/loadbalancer.py
Restart=always
RestartSec=3
StandardOutput=/var/log/simplelb_std_output.log
StandardError=/var/log/simplelb_error.log
[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to load the new service
sudo systemctl daemon-reload

# Enable and start the 'simplelb' service
sudo systemctl enable simplelb.service
sudo systemctl start simplelb.service
