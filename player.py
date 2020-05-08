import sys
import os

import mpv
from tcp_server import PlayerTCPServer


class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        print("Player: Created instance")
        # Init mpv player with options 
        self.mpv_player = mpv.MPV()
        self.mpv_player['hwdec'] = 'rpi'            # RPI decoder. Setting makes loading faster, as opposed to letting mpv decide 
        self.mpv_player['vo'] = 'rpi'               # RPI output. Same as above.
        self.mpv_player['cache'] = 'yes'            # Enable cache
        self.mpv_player['rpi-background'] = 'yes'   # Black background behind video
        self.mpv_player['rpi-osd'] = 'no'           # No OSD (On Screen Display) layer
        # self.mpv_player['merge-files'] = True       # Pretend that all files passed to mpv are concatenated into a single, big file.
        self.mpv_player['keep-open'] = 'yes'        # Do not terminate when playing or seeking beyond the end of the file
        self.mpv_player['idle'] = 'yes'             # Makes mpv wait idly instead of quitting when there is no file to play
        self.mpv_player['pause'] = True             # Start paused
        self.mpv_player.fullscreen = True           # Fullscreen

        self.video_path = '/home/pi/coin.mp4' # Test file
        self.mpv_player.loadfile(self.video_path)  

    def play_command(self):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing"""
        print('Player: Play command')
        self.mpv_player['loop-file'] = 'no'
        self.mpv_player['pause'] = False          

    def pause_command(self):
        """Pause command sent to player. 
        Pauses video if playing"""
        print('Player: Pause command')
        self.mpv_player['pause'] = True      

    def loop_command(self):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing"""
        print('Player: Loop command')
        self.mpv_player['loop-file'] = 'inf'
        self.mpv_player['pause'] = False  
        
    def quit(self):
        """Shuts down player"""
        print('Player: Shutdown')
        self.mpv_player.quit()