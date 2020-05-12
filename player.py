import mpv
from tcp_server import PlayerTCPServer
from pathlib import Path
import glob
import re

# Constant values. Return values for functions
LOAD_SUCCESS                = 1
LOAD_BAD_COMMAND            = 2
LOAD_NO_FILE                = 3

SEEK_SUCCESS                = 4
SEEK_BAD_FORM               = 5
SEEK_BAD_MM                 = 6
SEEK_BAD_SS                 = 7
SEEK_BAD_FF                 = 8
SEEK_TOO_LONG               = 9
SEEK_SUCCESS_FRAME_ERROR    = 10

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        print("Player: Creating instance")
        # Init mpv player with options 
        self.mpv_player = mpv.MPV(config=False) #, log_handler=print
        # self.mpv_player.set_loglevel('debug')
        self.mpv_player['hwdec'] = 'rpi'                    # RPI decoder. Setting makes loading faster, as opposed to letting mpv decide 
        self.mpv_player['vo'] = 'rpi'                       # RPI output. Same as above.
        self.mpv_player['demuxer-thread'] = 'yes'           # Run the demuxer in a separate thread
        self.mpv_player['demuxer'] = 'lavf'                 # libavformat Demuxer
        self.mpv_player['demuxer-lavf-probe-info'] = 'no'   # Whether to probe stream information
        self.mpv_player['cache'] = 'yes'                    # Enable cache
        self.mpv_player['demuxer-seekable-cache'] = 'yes'   # Seeking can use the demuxer cache
        # self.mpv_player['hr-seek'] = 'yes'                   # Use precise seeks whenever possible
        # self.mpv_player['hr-seek-framedrop'] = 'no'         # Do not allow the video decoder to drop frames during seek
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
    
    ################################################################################
    # Player command functions
    ################################################################################
    def load_command(self, msg_data):
        """Load command sent to player. 
        Loads video number sent to it"""
        print('Player: Load command')
        # Check if there is also a seek command in the load
        if re.search(r'SE.*', msg_data):
            load_command = re.sub(r'SE.*', ' ', msg_data)
            load_return_code = self._load_video(load_command)   
        else:
            # No seek command. Do load as normal
            load_return_code = self._load_video(msg_data)

        if load_return_code == LOAD_SUCCESS:
            if re.search(r'SE.*', msg_data):
                seek_time = re.findall(r'SE.*', msg_data)[0][2:]
                seek_return_code = self._seek_video(seek_time)
                if seek_return_code == SEEK_SUCCESS:
                    return 'Load and seek success'
                elif seek_return_code == SEEK_BAD_FORM:
                    return 'Load success. Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
                elif seek_return_code == SEEK_BAD_MM:
                    return 'Load success. Seek failure: mm must be between 00 and 59'
                elif seek_return_code == SEEK_BAD_SS:
                    return 'Load success. Seek failure: ss must be between 00 and 59'
                elif seek_return_code == SEEK_BAD_FF:
                    return 'Load success. Seek failure: ff must be between 00 and frame rate (' + str(self.mpv_player.container_fps) + ')'
                elif seek_return_code == SEEK_TOO_LONG:
                    return 'Load success. Seek failure: sent time is more than video duration'
                elif seek_return_code == SEEK_SUCCESS_FRAME_ERROR:
                    return 'Load success. Seek success with frame seek error. Ignored ff for seek'
            else:
                return 'Load success'
        elif load_return_code == LOAD_NO_FILE:
            return 'Load failure: Could not find file'
        elif load_return_code == LOAD_BAD_COMMAND:
            return 'Load failure: Incorrect file number sent'

        return 'Load failure: Unknown'

    def play_command(self, msg_data):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing
        Ignores message data"""
        print('Player: Play command')
        if self.mpv_player.idle_active == True:
            return 'Play failure: no file loaded'
    
        self.mpv_player['loop-file'] = 'no'
        self.mpv_player['pause'] = False     
        return 'Play success'     

    def pause_command(self, msg_data):
        """Pause command sent to player. 
        Pauses video if playing.
        Ignores message data"""
        print('Player: Pause command')
        if self.mpv_player.idle_active == True:
            return 'Pause failure: no file loaded'
    
        self.mpv_player['pause'] = True
        return 'Pause success' 

    def loop_command(self, msg_data):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing.
        Ignores message data"""
        print('Player: Loop command')
        if self.mpv_player.idle_active == True:
            return 'Loop failure: no file loaded'
        
        self.mpv_player['loop-file'] = 'inf'
        self.mpv_player['pause'] = False
        return 'Loop success' 

    def stop_command(self, msg_data):
        """Stop command sent to player.
        Stops playback, and clears playlist. 
        Essentially a quit without terminiating the player.
        Ignores message data"""
        print('Player: Stop command')
        if self.mpv_player.idle_active == True:
            return 'Stop failure: no file loaded'
        
        self.mpv_player.command('stop')
        return 'Stop success'

    def seek_command(self, msg_data):
        """Seek command sent to player.
        Seek to time passed in with message (in ms)"""
        print('Player: Seek command')
        if self.mpv_player.idle_active == True:
            return 'Seek failure: no file loaded'
        
        msg_data = msg_data.lstrip() # Remove leading whitespace

        self._seek_video(msg_data)
        if SEEK_SUCCESS:
            return 'Seek success'
        elif SEEK_BAD_FORM:
            return 'Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
        elif SEEK_BAD_MM:
            return 'Seek failure: mm must be between 00 and 59'
        elif SEEK_BAD_SS:
            return 'Seek failure: ss must be between 00 and 59'
        elif SEEK_BAD_FF:
            return 'Seek failure: ff must be between 00 and frame rate (' + str(self.mpv_player.container_fps) + ')'
        elif SEEK_TOO_LONG:
            return 'Seek failure: sent time is more than video duration'
        elif SEEK_SUCCESS_FRAME_ERROR:
            return 'Seek success with frame seek error. Ignored ff for seek'
        
    ################################################################################
    # Property Observer functions
    ################################################################################
    def idle_observer(self, _name, value):
        """Once we've become idle, clear the playlist"""
        if value == True:
            self.mpv_player.command('playlist-clear')

    
    ################################################################################
    # Utility functions
    ################################################################################
    def quit(self, *args):
        """Shuts down player
        Ignores any other arguments"""
        print('Player: Shutdown')
        self.mpv_player.quit()

    def _load_video(self, msg_data):
        """Loads video with passed in number"""
        # Remove whitespace
        msg_data = msg_data.lstrip()
        msg_data = msg_data.strip()
        # Try to convert msg data into a video number. If can't, throw error
        try:
            video_number = int(msg_data)
        except Exception as ex:
            print("Player: Load exception. Can't convert into number: " + str(ex))
            return LOAD_BAD_COMMAND

        # Search all correctly named video files for video number
        basepath = Path(self.video_folder)
        # Go through every file with 5 digits at the end of file name
        for video_file in basepath.glob('*[0-9][0-9][0-9][0-9][0-9].mp4'):
            # Extract number. Get number at end of file name, remove the file extension part, cast into an int
            file_number = int(re.findall(r'\d\d\d\d\d\.mp4', video_file.name)[0][0:5])
            if file_number == video_number:
                # We have a match. Load the file
                # Check if we currently idle. If so, replace the video
                if self.mpv_player.idle_active == True:
                    self.mpv_player.loadfile(str(video_file.resolve()), mode='replace')
                else:
                    self.mpv_player.loadfile(str(video_file.resolve()), mode='append')
                return LOAD_SUCCESS

        return LOAD_NO_FILE

    def _seek_video(self, seek_time):
        """Seeks to passed in seek time"""
        # Remove whitespace
        seek_time = seek_time.lstrip()
        seek_time = seek_time.strip()
        # Check time stamp is correct format
        if not re.match(r'^\d\d:\d\d:\d\d:\d\d$', seek_time):
            return SEEK_BAD_FORM
        
        timestamp_parts = seek_time.split(':')
       
        # Add hour seek time
        hours = int(timestamp_parts[0])
        seekTime = hours * 3600
        
        # Add minutes seek time
        mins = int(timestamp_parts[1])
        if mins > 59:
             return SEEK_BAD_MM
        seekTime = seekTime + (mins * 60)
        
        # Add seconds seek time
        seconds = int(timestamp_parts[2])
        if seconds > 59:
             return SEEK_BAD_SS
        seekTime = seekTime + (seconds)
        
        # Add frame seek time
        frames = int(timestamp_parts[3])
        frame_error = False
        try:
            container_fps = int(self.mpv_player.container_fps)
            if frames > container_fps:
                return SEEK_BAD_FF
            if frames != 0:
                seekTime = seekTime + ((1 / container_fps) * frames)
        except Exception as ex:
            print('Seek: frame seek error. Ignoring ff for seek: ' + str(ex))
            frame_error = True
        
        # Check if seek time is actually within the video duration 
        if seekTime > self.mpv_player.duration:
            return SEEK_TOO_LONG

        # Sikh
        self.mpv_player.seek(seekTime, reference='absolute', precision='exact')
        
        if frame_error:
            return SEEK_SUCCESS_FRAME_ERROR
        else:    
            return SEEK_SUCCESS
        

        
