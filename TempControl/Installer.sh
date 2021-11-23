#!/bin/bash

clear

echo "Instaling TempControl..."

sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install --upgrade setuptools
sudo apt-get install python3.7-dev
sudo python3 -m pip install sysv_ipc
sudo python3 -m pip install psutil
sudo python3 -m pip install thingspeak
sudo python3 -m pip install RPi.GPIO
sudo python3 fan.py -c
sudo python3 fan.py --install
sudo python3 fan.py --autoinit=true

echo "TempControl installed!"
