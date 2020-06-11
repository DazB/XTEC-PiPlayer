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

from web_server.server import run_web_server # pylint: disable=import-error
from mp2_details import config_path
from tcp_server import PlayerTCPServer
from player import Player
from digital_io import DigitalIO

class App:
    """Main Application class"""

    def __init__(self):
        """Initialise the application"""

        # Will use these default values if settings not present or incorrect
        ip = '192.168.1.105'
        port = '9999'
        subnet = '255.255.255.0'
        cidr = '24'
        gateway = '192.168.1.1'
        dns1 = '1.1.1.1'
        dns2 = '192.168.1.1'
        audio = 'both'
        devdesc = 'MP2 Default Description'
        input1_on = 'nothing'
        input1_on_track = '0'
        input1_off = 'nothing'
        input1_off_track = '0'
        input2_on = 'nothing'
        input2_on_track = '0'
        input2_off = 'nothing'
        input2_off_track = '0'

        try:
            # Go through config file and get / check settings.
            # If for whatever reason something is wrong or not there, it will use
            # default settings and write default to file
            config = configparser.ConfigParser()
            config.read(config_path)    # Will be empty if there is no file

            # If there isn't an MP2 section, add it
            if not config.has_section('MP2'):
                config['MP2'] = {}

            # IP address
            if config.has_option('MP2', 'ip'):
                if self.is_valid_ipv4(config['MP2']['ip']):
                    ip = config['MP2']['ip']
                else:
                    config['MP2']['ip'] = ip
            else:
                config['MP2']['ip'] = ip

            # Port number 
            if config.has_option('MP2', 'port'):
                if re.search(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$', config['MP2']['port']):
                    port = config['MP2']['port'] 
                else:
                    config['MP2']['port']  = port
            else:
                config['MP2']['port']  = port

            # Subnet mask 
            if config.has_option('MP2', 'subnet'):
                if self.is_valid_ipv4(config['MP2']['subnet']):
                    subnet = config['MP2']['subnet']
                    cidr = str(sum(bin(int(x)).count('1') for x in subnet.split('.')))
                else:
                    config['MP2']['subnet'] = subnet
            else:
                config['MP2']['subnet'] = subnet

            # Gateway 
            if config.has_option('MP2', 'gateway'):
                if self.is_valid_ipv4(config['MP2']['gateway']):
                    gateway = config['MP2']['gateway']
                else:
                    config['MP2']['gateway'] = gateway
            else:
                config['MP2']['gateway'] = gateway

            # DNS 1 
            if config.has_option('MP2', 'dns1'):
                if self.is_valid_ipv4(config['MP2']['dns1']):
                    dns1 = config['MP2']['dns1']
                else:
                    config['MP2']['dns1'] = dns1
            else:
                config['MP2']['dns1'] = dns1

            # DNS 2
            if config.has_option('MP2', 'dns2'):
                if self.is_valid_ipv4(config['MP2']['dns2']):
                    dns2 = config['MP2']['dns2']
                else:
                    config['MP2']['dns2'] = dns2
            else:
                config['MP2']['dns2'] = dns2

            # Audio 
            if config.has_option('MP2', 'audio'):
                if re.search(r'^hdmi$|^local$|^both$', config['MP2']['audio']):
                    audio = config['MP2']['audio']
                else:
                    config['MP2']['audio'] = audio
            else:
                config['MP2']['audio'] = audio

            # Device Description 
            if not config.has_option('MP2', 'devdesc'):
                config['MP2']['devdesc'] = devdesc
            
            # Input 1 on  
            if config.has_option('MP2', 'input1_on'):
                if not self.is_valid_io_command(config['MP2']['input1_on']):
                    config['MP2']['input1_on'] = input1_on
            else:
                config['MP2']['input1_on'] = input1_on

            # Input 1 off
            if config.has_option('MP2', 'input1_off'):
                if not self.is_valid_io_command(config['MP2']['input1_off']):
                    config['MP2']['input1_off'] = input1_off
            else:
                config['MP2']['input1_off'] = input1_off

            # Input 1 on track            
            if not config.has_option('MP2', 'input1_on_track'):
                config['MP2']['input1_on_track'] = input1_on_track

            # Input 1 off track
            if not config.has_option('MP2', 'input1_off_track'):
                config['MP2']['input1_off_track'] = input1_off_track

            # Input 2 on 
            if config.has_option('MP2', 'input2_on'):
                if not self.is_valid_io_command(config['MP2']['input2_on']):
                    config['MP2']['input2_on'] = input2_on
            else:
                config['MP2']['input2_on'] = input2_on

            # Input 2 off
            if config.has_option('MP2', 'input2_off'):
                if not self.is_valid_io_command(config['MP2']['input2_off']):
                    config['MP2']['input2_off'] = input2_off
            else:
                config['MP2']['input2_off'] = input2_off

            # Input 2 on track
            if not config.has_option('MP2', 'input2_on_track'):
                config['MP2']['input2_on_track'] = input2_on_track

            # Input 2 off track 
            if not config.has_option('MP2', 'input2_off_track'):
                config['MP2']['input2_off_track'] = input2_off_track

            # Write any changes potentially made to config file
            # If it doesn't exist, will create the file with the default values
            with open(config_path, 'w+') as configfile:
                config.write(configfile)

        except Exception as ex:
            print("Main: Config read exception: " + str(ex))
        
        # Edit the dhcpcd.conf file. This controls the network settings in the pi
        # Once edited, we reset the dhcpcd service to apply the settings
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
                file.writelines(data)

            # Apply changes to the eth0 network interface
            os.system('sudo ip addr flush dev eth0')
            os.system('sudo service dhcpcd restart')

        except Exception as ex:
            print("Error applying network settings: " + str(ex))

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

        # Create and start the tcp server
        # self.player_tcp_server = PlayerTCPServer(self.player, ip, port)
        
        # Start the webserver
        run_web_server(ip)

        # Start the Digital I/O
        self.digital_io = DigitalIO(self.player)

    def run(self):
        """Main app loop"""
        while True:
            time.sleep(10)

    def cleanup(self, signum, frame):
        """Application cleanup"""
        print('App: Cleaning up')
        # self.player_tcp_server.server.quit()
        self.player.quit()
        sys.exit('App: Quitting. Goodbye')

    def is_valid_ipv4(self, ip):
        """A little regex to check if the ip is valid ipv4"""
        return re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip) 
    
    def is_valid_io_command(self, command):
        """A little regex to check if the IO command is valid"""
        return re.search(r'^nothing$|^play$|^loop$|^random$|^stop$|^pause$|^audio_mute$|^video_mute$|^audio_unmute$|^video_unmute$', command) 


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
