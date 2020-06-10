#!/usr/bin/env python3

#######################################
## Pi Player
#######################################

import sys
import signal
import time
import logging
import configparser
import re
import os

# from web_server.server import run_web_server
from tcp_server import PlayerTCPServer
from player import Player

class App:
    """Main Application class"""

    def __init__(self):
        """Creates all the application objects"""

        # Get config settings. Will use default values if settings not present or incorrect
        ip = '192.168.1.105'
        port = '9999'
        subnet = '255.255.255.0'
        cidr = '24'
        gateway = '192.168.1.1'
        dns1 = '8.8.8.8'
        dns2 = '192.168.1.1'

        audio = 'both'

        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            mp2_config = config['MP2']
            # IP address
            if mp2_config['ip'] != None:
                if re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', mp2_config['ip']):
                    ip = mp2_config['ip']
            # Port number 
            if mp2_config['port'] != None:
                if re.search(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$', mp2_config['port']):
                    port = mp2_config['port']
            # Subnet mask 
            if mp2_config['subnet'] != None:
                if re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', mp2_config['subnet']):
                    subnet = mp2_config['subnet']
                    cidr = str(sum(bin(int(x)).count('1') for x in subnet.split('.')))
            # Audio 
            if mp2_config['audio'] != None:
                if re.search(r'^audio$|^local$|^both$', mp2_config['audio']):
                    audio = mp2_config['audio']

        except Exception as ex:
            print("Main: Config read exception: " + str(ex))
        
        # Edit the dhcpcd.conf file. This controls the network settings in the pi
        conf_file = '/etc/dhcpcd.conf'
        try:            
            # Sanitize/validate params above
            with open(conf_file, 'r') as file:
                data = file.readlines()

            # Find if config exists
            ethFound = next((x for x in data if 'interface eth0' in x), None)

            if ethFound:
                ethIndex = data.index(ethFound)
                if data[ethIndex].startswith('#'):
                    data[ethIndex].replace('#', '') # commented out by default, make active

            # If config is found, use index to edit the lines you need ( the next 3)
            if ethIndex:
                data[ethIndex+1] = f'static ip_address={ip}/{cidr}\n'
                data[ethIndex+2] = f'static routers={gateway}\n'
                data[ethIndex+3] = f'static domain_name_servers={dns1} {dns2}\n'

            with open(conf_file, 'w') as file:
                file.writelines( data )

        except Exception as ex:
            logging.exception("Network changing error: %s", ex)

        # # Apply changes to the eth0 network interface
        os.system('sudo ip addr flush dev eth0')
        os.system('sudo service dhcpcd restart')
        # os.system('sudo ip link set eth0 down')
        # os.system('sudo ip addr change ' + ip + '/' + subnet + ' dev eth0')
        # os.system('sudo ip route del default')
        # os.system('sudo ip route add default via ' + gateway)
        # os.system('sudo ip link set eth0 up')

        # Try to create the player
        self.player = None
        player_retry = 0
        PLAYER_RETRY_DELAY = 2
        PLAYER_MAX_RETRIES = 5
        while self.player is None:
            try:
                self.player = Player()   # Video player instance
            except Exception as ex:
                if player_retry == PLAYER_MAX_RETRIES:
                    sys.exit('Cannot create Player. Is the path correct? : %s' % ex)
                player_retry += 1
                print('Attempt %d. Error in creating player: %s' % (player_retry, ex))
                time.sleep(PLAYER_RETRY_DELAY)

        # Create the tcp server
        # self.player_tcp_server = PlayerTCPServer(self.player, ip, port)
        
        # Run the webserver
        # run_web_server(ip)

    def run(self):
        """Main app loop"""
        while True:
            time.sleep(10)

    def cleanup(self, signum, frame):
        """Application cleanup"""
        print('App: Cleaning up')
        self.player_tcp_server.server.quit()
        self.player.quit()
        sys.exit('App: Quitting. Goodbye')     


# Main entry point.
if __name__ == '__main__':
    print('And here we go....')

    # LOG_FILENAME = 'debug.log'
    # logging.basicConfig(
    #     filename=LOG_FILENAME,
    #     format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    #     datefmt='%H:%M:%S',
    #     level=logging.DEBUG)

    # Main app instance
    app = App()

    # Sets app exit signals to call cleanup
    signal.signal(signal.SIGINT, app.cleanup)
    signal.signal(signal.SIGTERM, app.cleanup)

    # Run the app :D
    app.run()
