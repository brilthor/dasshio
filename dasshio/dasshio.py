#!/usr/bin/env python3

import json
import logging
import os
import requests
from scapy.all import sniff
from scapy.all import ARP
from scapy.all import UDP
from scapy.all import IP
from scapy.all import DHCP
from scapy.all import Ether
import sys
import time
import signal

def signal_handler(signal, frame):
    sys.exit(0)

def arp_display(pkt):
    mac = ""
    matched_button = False
    try:
        mac = pkt[ARP].hwsrc.lower()
    except:
        mac = pkt[Ether].src.lower()

    for button in config['buttons']:
        if mac == button['address'].lower():

            idx = [button['address'].lower() for button in config['buttons']].index(mac)
            button = config['buttons'][idx]

            logging.info(button['name'] + " button pressed!")
            matched_button = True
            logging.info("Request: " + button['url'])
            
            try:
                request = requests.post(button['url'], json=json.loads(button['body']), headers=json.loads(button['headers']))
                logging.info('Status Code: {}'.format(request.status_code))
                
                if request.status_code == requests.codes.ok:
                    logging.info("Successful request")
                else:
                    logging.error("Bad request")
            except:
                logging.exception("Unable to perform  request: Check url, body and headers format. Check API password")

    if matched_button:
        logging.info("Packet captured, waiting 3s ...")
        time.sleep(3)

    return matched_button

# Catch SIGINT/SIGTERM Signals
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
    
# Remove Scapy IPv6 warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Create basepath
path = os.path.dirname(os.path.realpath(__file__))

# Log events to stdout
logger = logging.getLogger()
logger.setLevel(logging.INFO)

stdoutHandler = logging.StreamHandler(sys.stdout)
stdoutHandler.setLevel(logging.INFO)

formater = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
stdoutHandler.setFormatter(formater)

logger.addHandler(stdoutHandler)

# Read config file
logging.info("Reading config file: /data/options.json")

with open(path + '/data/options.json', mode='r') as data_file:
    config = json.load(data_file)

while True:
    # Start sniffing
    logging.info("Starting sniffing...")
    sniff(stop_filter=arp_display, iface=config['iface'], filter='arp or (udp and src port 68 and dst port 67 and src host 0.0.0.0)', store=0, count=0)
    
