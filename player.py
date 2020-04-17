import sys
import time
import os
from threading import Timer

from omxplayer.player import OMXPlayer
from tcp_server import PlayerTCPServer

# Constants
# Video player layers
VISIBLE_LAYER = 2
HIDDEN_LAYER = 1

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        self.video_path = "/home/pi/VideoPlayer/testfiles/bbb_sunflower_1080p_30fps_normal_Trim.mp4" # Test file
        # Init 2 OMX players
        self.omxplayer_1 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b', '-g'])
        self.omxplayer_2 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer2', pause=True, args=['--no-osd', '--no-keys', '-b', '-g'])
        # Assign playeres to variables to make clear which ones are shown and hidden.
        self.visible_player = self.omxplayer_1
        self.hidden_player = self.omxplayer_2
        # Set layer of players so we show the correct one
        self.visible_player.set_layer(VISIBLE_LAYER)
        self.hidden_player.set_layer(HIDDEN_LAYER)
        
        # Event timer used to determine end of video. Set on play
        # self.video_end_timer = Timer(0, None)

        # Other player variables
        self.loop = False
        

    def run(self):
        pass

    def play_command(self):
        print('Player: Play command')
        self.loop = False
        if not self.visible_player.is_playing():
            self._play()

    def loop_command(self):
        print('Player: Loop')
        
        self.loop = True
        self.visible_player.set_loop(self.loop)

        if not self.visible_player.is_playing():
            self._play()

    def quit(self):
        """Shut down player"""
        # self.video_end_timer.cancel()
        self.omxplayer_1.quit()
        self.omxplayer_2.quit()
        print('Player: Shutdown')

    ######################### Class utility functions ##################################

    def _play(self):
        # self.video_end_timer = Timer(self.visible_player.duration(), self._end_of_video)
        # self.video_end_timer.start()
        self.visible_player.play()

    def _end_of_video(self):
        print('Player: End of video')
        # if self.loop:
        #     self.visible_player.set_position(0)
        #     self._play()
        # else:
        # Show the preloaded hidden player
        self.hidden_player.set_layer(VISIBLE_LAYER)
        self._switch_players()
        self._load_new_player_hidden()

    def _switch_players(self):
        """Switches players. Visible becomes Hidden and Hidden becomes Visible"""
        if self.visible_player == self.omxplayer_1:
            self.visible_player = self.omxplayer_2
            self.hidden_player = self.omxplayer_1
        else:
            self.visible_player = self.omxplayer_1
            self.hidden_player = self.omxplayer_2

    def _load_new_player_hidden(self):
        if self.hidden_player == self.omxplayer_1:
            self.omxplayer_1.quit()
            self.omxplayer_1 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self.omxplayer_1
        else:
            self.omxplayer_2.quit()
            self.omxplayer_2 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer2', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self.omxplayer_2
        
        self.hidden_player.set_layer(HIDDEN_LAYER)