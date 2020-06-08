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

from tcp_server import PlayerTCPServer
from player import Player

class App:
    """Main Application class"""

    def __init__(self):
        """Creates all the application objects"""

        # Get config settings. Will use default values if settings not present or incorrect
        ip = '0.0.0.0'
        port = '9999'
        subnet = '255.255.255.0'
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

        except Exception as ex:
            print("Main: Config read exception: " + str(ex))
        
        os.system('sudo ifconfig eth0 down')
        os.system('sudo ifconfig eth0 ' + ip + ' netmask ' + subnet)
        os.system('sudo ifconfig eth0 up')

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

        # Create the server
        self.player_tcp_server = PlayerTCPServer(self.player, ip, port)

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
