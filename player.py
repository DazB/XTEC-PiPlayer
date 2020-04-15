#!/usr/bin/env python3

#######################################
## Pi Player
#######################################

import sys
import signal
import sched
import time
import os
import logging
from time import sleep
from threading import Timer

from omxplayer.player import OMXPlayer
from tcp_server import PlayerTCPServer


class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        self.video_path = "/home/pi/VideoPlayer/testfiles/bbb_sunflower_1080p_30fps_normal_Trim.mp4" # Test file
        self.omxplayer = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])
        self.player_end_timer = Timer(None, None)

    def run(self):
        pass

    def play(self):
        print('Player sent play command')
        self.player_end_timer = Timer(self.omxplayer.duration(), self.end_of_video)
        self.player_end_timer.start()
        self.omxplayer.play()

    def end_of_video(self):
        print('Video ended')
        self.omxplayer.load(self.video_path, pause=True)
        self.play()

    def quit(self):
        """Shut down program"""
        self.player_end_timer.cancel()
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
    print('And here we go....')
    LOG_FILENAME = 'debug.log'
    logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

    # Sets exit signals to call cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
  
    # Try to create the player
    player = None
    player_retry = 0
    PLAYER_RETRY_DELAY = 2
    PLAYER_MAX_RETRIES = 5
    while player is None:
        try:
            player = Player()   # Video player instance
        except Exception as ex:
            if player_retry == PLAYER_MAX_RETRIES:
                sys.exit('Cannot create Player. Is the path correct? : %s' % ex)
            player_retry += 1
            print('Attempt %d. Error in creating player: %s' % (player_retry, ex))
            sleep(PLAYER_RETRY_DELAY)

    # Create the server
    player_tcp_server = PlayerTCPServer(player)

    while True:
        pass
