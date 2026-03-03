#!/bin/bash

# Update apt packages
apt-get update

# Install Chromium along with its required dependencies
apt-get install -y chromium-browser chromium-chromedriver

ln -s /usr/bin/chromedriver /usr/bin/chromium-driver

# Python dependencies for the mcp to run
pip install -r requirements.txt
