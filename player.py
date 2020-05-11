import mpv
from tcp_server import PlayerTCPServer
from pathlib import Path
import glob
import re

# Constant values
LOAD_SUCCESS = 1
LOAD_FAILURE = 2

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        print("Player: Creating instance")
        # Init mpv player with options 
        self.mpv_player = mpv.MPV(config=False, log_handler=print) #, log_handler=print
        # self.mpv_player.set_loglevel('debug')
        self.mpv_player['hwdec'] = 'rpi'                    # RPI decoder. Setting makes loading faster, as opposed to letting mpv decide 
        self.mpv_player['vo'] = 'rpi'                       # RPI output. Same as above.
        self.mpv_player['demuxer-thread'] = 'yes'           # Run the demuxer in a separate thread
        self.mpv_player['demuxer'] = 'lavf'                 # libavformat Demuxer
        self.mpv_player['demuxer-lavf-probe-info'] = 'no'   # Whether to probe stream information
        self.mpv_player['cache'] = 'yes'                    # Enable cache
        self.mpv_player['demuxer-seekable-cache'] = 'yes'   # Seeking can use the demuxer cache
        # self.mpv_player['hr-seek'] = 'yes'                   # Use precise seeks whenever possible
        self.mpv_player['hr-seek-framedrop'] = 'no'         # Do not allow the video decoder to drop frames during seek
        self.mpv_player['vf'] = 'null'                      # No videofilters. Speeds up looping and loading explicitly stating it
        self.mpv_player['rpi-background'] = 'yes'           # Black background behind video
        self.mpv_player['rpi-osd'] = 'no'                   # No OSD (On Screen Display) layer
        # self.mpv_player['keep-open'] = 'yes'                # Do not terminate when playing or seeking beyond the end of the file
        self.mpv_player['prefetch-playlist'] = 'yes'        # Prefetch next playlist entry while playback of the current entry is ending
        self.mpv_player['idle'] = 'yes'                     # Makes mpv wait idly instead of quitting when there is no file to play
        self.mpv_player['pause'] = True                     # Start paused
        self.mpv_player.fullscreen = True                   # Fullscreen
        self.mpv_player['ontop'] = True                     # Makes the player window stay on top of other windows.
        self.mpv_player['force-window'] = 'yes'             # Create a video output window even if there is no video

        # Assign property observers that call functions when a property changes
        self.mpv_player.observe_property('idle-active', self.idle_observer)

        self.video_folder = '/home/pi/'
        # self.video_path = '/home/pi/coin.mp4' # Test file
        # self.mpv_player.loadfile(self.video_path)  
        
    def load_command(self, msg_data):
        """Load command sent to player. 
        Loads video number sent to it"""
        if self._load_video(msg_data) == LOAD_SUCCESS:
            print('Loaded video')
        else:
            print('Error loading video')

    def play_command(self, msg_data):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing
        Ignores message data"""
        print('Player: Play command')
        self.mpv_player['loop-file'] = 'no'
        self.mpv_player['pause'] = False          

    def pause_command(self, msg_data):
        """Pause command sent to player. 
        Pauses video if playing.
        Ignores message data"""
        print('Player: Pause command')
        self.mpv_player['pause'] = True      

    def loop_command(self, msg_data):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing.
        Ignores message data"""
        print('Player: Loop command')
        self.mpv_player['loop-file'] = 'inf'
        self.mpv_player['pause'] = False  
        
    def quit(self, *args):
        """Shuts down player
        Ignores any other arguments"""
        print('Player: Shutdown')
        self.mpv_player.quit()

    ################################################################################
    # Property Observer functions
    ################################################################################
    def idle_observer(self, _name, value):
        """Once we've become idle, clear the playlist"""
        if value == True:
            self.mpv_player.command('playlist-clear')

    
    ################################################################################
    # Class utility functions
    ################################################################################
    def _load_video(self, msg_data):
        """Loads video with passed in number"""
        msg_data.lstrip() # Remove leading or trailing whitespace
        # Try to convert msg data into a video number. If can't, throw error
        try:
            video_number = int(msg_data)
        except Exception as ex:
            print("Player: Load exception. Can't convert into number: " + str(ex))
            return LOAD_FAILURE

        # Search all correctly named video files for video number
        basepath = Path(self.video_folder)
        # Go through every file with 5 digits at the end of file name
        for video_file in basepath.glob('*[0-9][0-9][0-9][0-9][0-9].mp4'):
            # Extract number. Get number at end of file name, remove the file extension part, cast into an int
            file_number = int(re.search(r'\d\d\d\d\d\.mp4', video_file.name).group(0)[0:5])
            if file_number == video_number:
                # We have a match. Load the file
                # Check if we currently idle. If so, replace the video
                if self.mpv_player.idle_active == True:
                    self.mpv_player.loadfile(str(video_file.resolve()), mode='replace')
                else:
                    self.mpv_player.loadfile(str(video_file.resolve()), mode='append')
                return LOAD_SUCCESS

        return LOAD_FAILURE

        

        
