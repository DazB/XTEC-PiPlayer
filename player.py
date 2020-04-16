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

# Constants
# Video player layers
TOP_LAYER = 3
MIDDLE_LAYER = 2
BOTTOM_LAYER = 1

class Player:
    """Main video player class"""

    quitting = False

    def __init__(self):
        """Create an instance of the main video player application class"""
        self.video_path = "/home/pi/VideoPlayer/testfiles/bbb_sunflower_1080p_30fps_normal_Trim.mp4" # Test file
        # Init 2 OMX players
        self._omxplayer_1 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])
        self._omxplayer_2 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer2', pause=True, args=['--no-osd', '--no-keys', '-b'])
        # Assign playeres to variables to make clear which ones are shown and hidden.
        self.shown_player = self._omxplayer_1
        self.hidden_player = self._omxplayer_2
        # Set layer of players so we show the correct one
        self.shown_player.set_layer(TOP_LAYER)
        self.hidden_player.set_layer(BOTTOM_LAYER)
        
        self.loop = True

    def run(self):
        pass

    def play(self):
        print('Player sent play command')
        self.shown_player.play()
        self.shown_player.exitEvent = self.end_of_video

    def end_of_video(self, player, exit_status):
        print('Video ended')
        # Check we're not quitting the player
        if not self.quitting:
            self.switch_layers()

            if self.loop:
                self.play()
            
            self.load_new_player_hidden()
            self.shown_player.set_layer(MIDDLE_LAYER)

    def load_new_player_hidden(self):
        if self.hidden_player == self._omxplayer_1:
            self._omxplayer_1 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self._omxplayer_1
        else:
            self._omxplayer_2 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer2', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self._omxplayer_2
        
        self.hidden_player.set_layer(BOTTOM_LAYER)


    def switch_layers(self):
        """Switches players. Shown becomes Hidden and Hidden becomes Shown"""
        if self.shown_player == self._omxplayer_1:
            self.shown_player = self._omxplayer_2
            self.hidden_player = self._omxplayer_1
        else:
            self.shown_player = self._omxplayer_1
            self.hidden_player = self._omxplayer_2

        # Show the new shown player
        self.shown_player.set_layer(TOP_LAYER)

    def quit(self):
        """Shut down program"""
        Player.quitting = True
        self._omxplayer_1.quit()
        self._omxplayer_2.quit()
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
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

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
