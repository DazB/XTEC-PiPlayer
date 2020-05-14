import mpv
from tcp_server import PlayerTCPServer
from pathlib import Path
import glob
import re
import enum
import subprocess
import shlex
import json
from asteval import Interpreter
import time

# Load return codes 
class Load_Result(enum.Enum): 
    LOAD_SUCCESS = 1
    LOAD_BAD_COMMAND = 2
    LOAD_NO_FILE = 3

# Seek return codes 
class Seek_Result(enum.Enum): 
    SEEK_SUCCESS                = 1
    SEEK_BAD_FORM               = 2
    SEEK_BAD_MM                 = 3
    SEEK_BAD_SS                 = 4
    SEEK_BAD_FF                 = 5
    SEEK_TOO_LONG               = 6
    SEEK_SUCCESS_FRAME_ERROR    = 7

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        print("Player: Creating instance")
        # Init mpv player with config file
        self.mpv_player = mpv.MPV(config=True, config_dir='./', log_handler=print) #
        self.mpv_player.set_loglevel('debug')

        # Assign property observers that call functions when a property changes
        self.mpv_player.observe_property('idle-active', self.idle_observer)

        # Main folder where all videos are kept
        self.video_folder = 'testfiles/' # TODO: this will obvs change

    ################################################################################
    # Player command functions
    ################################################################################
    def load_command(self, msg_data):
        """Load command sent to player.
        Loads video number sent to it. Can also be combined with seek command to seek 
        to specific position in loaded video."""
        print('Player: Load command')       
        load_return_code, seek_return_code = self._load_video(msg_data)

        if load_return_code == Load_Result.LOAD_SUCCESS:
            # Was there also a seek when loading?
            if seek_return_code != None:
                if seek_return_code == Seek_Result.SEEK_SUCCESS:
                    return 'Load and seek success'
                elif seek_return_code == Seek_Result.SEEK_SUCCESS_FRAME_ERROR:
                    return 'Load success. Seek success with frame seek error. Ignored ff for seek'
                elif seek_return_code == Seek_Result.SEEK_BAD_FORM:
                    return 'File not loaded. Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
                elif seek_return_code == Seek_Result.SEEK_BAD_MM:
                    return 'File not loaded. Seek failure: mm must be between 00 and 59'
                elif seek_return_code == Seek_Result.SEEK_BAD_SS:
                    return 'File not loaded. Seek failure: ss must be between 00 and 59'
                elif seek_return_code == Seek_Result.SEEK_BAD_FF:
                    return 'File not loaded. Seek failure: ff must be between 00 and frame rate (' + str(self.mpv_player.container_fps) + ')'
                elif seek_return_code == Seek_Result.SEEK_TOO_LONG:
                    return 'File not loaded. Seek failure: sent time is more than video duration'
            else:
                return 'Load success'
        elif load_return_code == Load_Result.LOAD_NO_FILE:
            return 'Load failure: Could not find file'
        elif load_return_code == Load_Result.LOAD_BAD_COMMAND:
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
        # self.mpv_player.command('vf', 'set', 'loop=loop=-1:size=' + str(self.mpv_player.estimated_frame_count))
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
        # Get seek time in seconds and result code
        seek_result_code, seek_time_secs = self._get_seek_time(msg_data, self.mpv_player.container_fps, self.mpv_player.duration)
        # Check result of getting the seek time
        if seek_result_code == Seek_Result.SEEK_SUCCESS:
            # Sikh
            self.mpv_player.seek(seek_time_secs, reference='absolute', precision='exact')
            return 'Seek success'
        elif seek_result_code == Seek_Result.SEEK_BAD_FORM:
            return 'Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
        elif seek_result_code == Seek_Result.SEEK_BAD_MM:
            return 'Seek failure: mm must be between 00 and 59'
        elif seek_result_code == Seek_Result.SEEK_BAD_SS:
            return 'Seek failure: ss must be between 00 and 59'
        elif seek_result_code == Seek_Result.SEEK_BAD_FF:
            return 'Seek failure: ff must be between 00 and frame rate (' + str(self.mpv_player.container_fps) + ')'
        elif seek_result_code == Seek_Result.SEEK_TOO_LONG:
            return 'Seek failure: sent time is more than video duration'
        elif seek_result_code == Seek_Result.SEEK_SUCCESS_FRAME_ERROR:
            return 'Seek success with frame seek error. Ignored ff for seek'

    def video_mute_command(self, msg_data):
        """Video mute command sent to player.
        Mutes """
        print('Player: Video Mute command')
        mute_option = 0
        try:
            mute_option = int(msg_data)
        except Exception as ex:
            return 'Video Mute error: incorrect option sent: ' + str(ex)
        
        if mute_option == 0:
            self.mpv_player.command('vf', 'set', '')
            return 'Video Mute success: video unmuted'
        elif mute_option == 1:
            self.mpv_player.command('vf', 'set', 'drawbox=x=0:y=0:w=1920:h=1080:color=black:t=fill') # TODO: using 1920x1080. Correct?
            # self.mpv_player.command('vf', 'set', 'drawbox=x=0:y=0:w=' + str(self.mpv_player.dwidth) + ':h=' + str(self.mpv_player.dheight) + ':color=black:t=fill')
            return 'Video Mute success: video muted'
        else:
            return 'Video Mute error: specify 0 for unmute and 1 for mute'
        
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
        """Loads video. Will also perform seek if there is a seek command included"""
        # Remove whitespace
        msg_data = msg_data.lstrip()
        msg_data = msg_data.strip()
        
        # Check if there is also a seek command with the load
        seek = False
        if re.search(r'SE.*', msg_data):
            load_command = re.sub(r'SE.*', ' ', msg_data)
            seek = True
        else:
            # No seek command
            load_command = msg_data

        # Try to convert msg data into a video number. If can't, throw error
        try:
            video_number = int(load_command)
        except Exception as ex:
            print("Player: Load exception. Can't convert into number: " + str(ex))
            return Load_Result.LOAD_BAD_COMMAND, None

        # Search all correctly named video files for video number
        basepath = Path(self.video_folder)
        # Go through every file with 5 digits at the end of file name
        for video_file in basepath.glob('*[0-9][0-9][0-9][0-9][0-9].mp4'):
            # Extract number. Get number at end of file name, remove the file extension part, cast into an int
            file_number = int(re.findall(r'\d\d\d\d\d\.mp4', video_file.name)[0][0:5])
            # Check if we have a match
            if file_number == video_number:
                # We have a match. Are we seeking?
                if not seek:
                    # Load video with no seek. Check if we currently idle. If so, replace the video
                    if self.mpv_player.idle_active == True:
                        self.mpv_player.loadfile(str(video_file.resolve()), mode='replace')
                    else:
                        self.mpv_player.loadfile(str(video_file.resolve()), mode='append')
                    return Load_Result.LOAD_SUCCESS, None
                else:
                    # We are loading this file with a seek.
                    # To do seek, we need to pass the video frames and duration. We use ffprobe to get
                    # this info without loading the video
                    fps, duration = self._get_fps_duration_metadata(str(video_file.resolve()))
                    seek_timestamp = re.sub(r'.* SE', ' ', msg_data)
                    seek_result, seek_time_secs = self._get_seek_time(seek_timestamp, fps, duration)

                    if (seek_result == Seek_Result.SEEK_SUCCESS) or (seek_result == Seek_Result.SEEK_SUCCESS_FRAME_ERROR):
                        # Check if we currently idle. If so, replace the video. 
                        # We are using our seek time to say where to start video .
                        if self.mpv_player.idle_active == True:
                            self.mpv_player.loadfile(str(video_file.resolve()), mode='replace', start=str(seek_time_secs))
                        else:
                            self.mpv_player.loadfile(str(video_file.resolve()), mode='append', start=str(seek_time_secs))
                    
                    return Load_Result.LOAD_SUCCESS, seek_result

        return Load_Result.LOAD_NO_FILE, None

    def _get_seek_time(self, seek_time, video_frames, video_duration):
        """Gets seek time passed in seconds. Returns result. Done this way because in the case of LD, 
        we may want to do a seek for a video that isn't this one"""
        # Remove whitespace
        seek_time = seek_time.lstrip()
        seek_time = seek_time.strip()
        # Check time stamp is correct format
        if not re.match(r'^\d\d:\d\d:\d\d:\d\d$', seek_time):
            return Seek_Result.SEEK_BAD_FORM, 0
        
        timestamp_parts = seek_time.split(':')
       
        # Add hour seek time
        seek_hours = int(timestamp_parts[0])
        seek_time_secs = seek_hours * 3600
        
        # Add minutes seek time
        seek_mins = int(timestamp_parts[1])
        if seek_mins > 59:
             return Seek_Result.SEEK_BAD_MM, 0
        seek_time_secs = seek_time_secs + (seek_mins * 60)
        
        # Add seconds seek time
        seek_seconds = int(timestamp_parts[2])
        if seek_seconds > 59:
             return Seek_Result.SEEK_BAD_SS, 0
        seek_time_secs = seek_time_secs + (seek_seconds)
        
        # Add frame seek time
        seek_frames = int(timestamp_parts[3])
        frame_error = False
        
        if video_frames == 0:
            print('Seek: frame seek error. Ignoring ff for seek')
            frame_error = True        
        else:
            if seek_frames > video_frames:
                return Seek_Result.SEEK_BAD_FF, 0
            else:
                seek_time_secs = seek_time_secs + ((1 / video_frames) * seek_frames)
        
        # Check if seek time is actually within the video duration 
        if seek_time_secs > video_duration:
            return Seek_Result.SEEK_TOO_LONG, 0
       
        if frame_error:
            return Seek_Result.SEEK_SUCCESS_FRAME_ERROR, seek_time_secs
        else:
            return Seek_Result.SEEK_SUCCESS, seek_time_secs
        
    def _get_fps_duration_metadata(self, videopath):
        """Function to find the fps and duration of the input video file"""
        cmd = "ffprobe -v quiet -print_format json -show_streams"
        args = shlex.split(cmd)
        args.append(videopath)
        # run the ffprobe process, decode stdout into utf-8 & convert to JSON
        ffprobeOutput = subprocess.check_output(args).decode('utf-8')
        ffprobeOutput = json.loads(ffprobeOutput)

        # try get fps and duration
        fps = 0
        duration = 0
        try:
            duration = float(ffprobeOutput['streams'][0]['duration'])
            aeval = Interpreter()
            fps = aeval(ffprobeOutput['streams'][0]['avg_frame_rate'])
        except Exception as ex:
            print('Error getting metadata: ' + str(ex))

        return fps, duration
    
        

        
