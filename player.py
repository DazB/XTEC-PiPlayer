import sys
import time
import os
import threading

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
        # Visable player has started playing video
        self.playing_in_progress = False
        # Event timer used to determine end of video. Set on play
        # self.video_end_timer = Timer(0, None)       

    def play_command(self):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing"""
        print('Player: Play command')
        self.visible_player.set_loop(False)
        if not self.visible_player.is_playing():
            if self.playing_in_progress == False:
                self._play_from_start()
            else:
                self.visible_player.play()
            

    def pause_command(self):
        """Pause command sent to player. 
        Pauses video if playing"""
        print('Player: Pause command')
        if self.visible_player.is_playing():
            self.visible_player.pause()

    def loop_command(self):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing"""
        print('Player: Loop')
        self.visible_player.set_loop(True)
        if not self.visible_player.is_playing():
            self._play_from_start()

    def quit(self):
        """Shuts down player"""
        # self.video_end_timer.cancel()
        self.omxplayer_1.quit()
        self.omxplayer_2.quit()
        print('Player: Shutdown')

    ######################### Class utility functions ##################################

    def _play_from_start(self):
        """Plays video, and starts thread to check for end of video"""
        # self.video_end_timer = Timer(self.visible_player.duration(), self._end_of_video)
        # self.video_end_timer.start()
        # self.visible_player.play()
        self.visible_player.play()
        self.playing_in_progress = True
        wait_end_thread = threading.Thread(target=self._wait_until_end)
        wait_end_thread.daemon = True
        wait_end_thread.start()

    def _wait_until_end(self):
        """Will constantly poll currently playing media to check if it's stopped"""
        try:
            while self.visible_player.playback_status() != "Stopped":
                time.sleep(0.01)
        except Exception as ex:
            print('_wait_until_end exception. Most likely player shutdown becuase of end of video, ' + 
            'which is expected: %s', ex)
        finally:
            self._end_of_video()

    def _end_of_video(self):
        """On end of video, switch player layers"""
        print('Player: End of video')
        # Show the preloaded hidden player
        self.hidden_player.set_layer(VISIBLE_LAYER)
        self._switch_players()
        self._load_new_player_hidden()
        # No longer playing
        self.playing_in_progress = False 

    def _switch_players(self):
        """Switches players. Visible becomes Hidden and Hidden becomes Visible"""
        if self.visible_player == self.omxplayer_1:
            self.visible_player = self.omxplayer_2
            self.hidden_player = self.omxplayer_1
        else:
            self.visible_player = self.omxplayer_1
            self.hidden_player = self.omxplayer_2

    def _load_new_player_hidden(self):
        """Loads the media for the hidden player"""
        if self.hidden_player == self.omxplayer_1:
            # self.omxplayer_1.quit() Because old player will die, don't need to quit. Just let it die
            self.omxplayer_1 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self.omxplayer_1
        else:
            self.omxplayer_2 = OMXPlayer(self.video_path, dbus_name='org.mpris.MediaPlayer2.omxplayer2', pause=True, args=['--no-osd', '--no-keys', '-b'])
            self.hidden_player = self.omxplayer_2
        
        self.hidden_player.set_layer(HIDDEN_LAYER)