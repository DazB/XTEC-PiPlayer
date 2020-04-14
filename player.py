#!/usr/bin/env python3

#######################################
## Pi Player
#######################################

from omxplayer.player import OMXPlayer
from pathlib import Path
import sys
from time import sleep
import signal
# import socketserver
# import socket
# import threading
from tcp_server import PlayerTCPServer


class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        self.path = "/opt/vc/src/hello_pi/hello_video/test.h264" # Test file
        self.omxplayer = OMXPlayer(self.path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])

    def run(self):
        pass

    def play(self):
        print('Player sent play command')
        self.omxplayer.play()

    def quit(self):
        """Shut down program"""
        self.omxplayer.quit()
        print('Player Shutdown')

def cleanup(signum, frame):
    """Cleanup function. Calls cleanup functions in each class"""
    print('Cleaning up')
    player_tcp_server.server.quit()
    player.quit()
    sys.exit('Quitting program')

# Main entry point.
if __name__ == '__main__':
    print('Here we go....')
    # Sets exit signals to call cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
  
    try:
        player = Player()   # Video player instance
    except Exception as ex:
        sys.exit('Unexpected error starting player: %s' % ex)

    # Create the server
    player_tcp_server = PlayerTCPServer(player)

    while True:
        pass
