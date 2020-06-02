from tcp_server import PlayerTCPServer
from omxplayer.player import OMXPlayer

from pathlib import Path
import glob
import re
import enum
import subprocess
import shlex
import json
from asteval import Interpreter
import time
import numpy as np
from evento import Event
import threading

# Constants
# Video player layers
LAYER_LOADING   = 1
LAYER_UNMUTE    = 2
LAYER_LOOP      = 3
LAYER_PLAYING   = 4
LAYER_MUTE      = 5

class Load_Result(enum.Enum):
    """Load return codes """
    SUCCESS                = 1
    BAD_COMMAND            = 2
    NO_FILE                = 3
    FILE_ALREADY_PLAYING   = 4

class Seek_Result(enum.Enum): 
    """Seek return codes """
    SUCCESS                = 1
    BAD_FORM               = 2
    BAD_MM                 = 3
    BAD_SS                 = 4
    BAD_FF                 = 5
    TOO_LONG               = 6
    SUCCESS_FRAME_ERROR    = 7

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        print("Player: Creating instance")
        # First, we create a player that plays a black screen and stops. This is a little bit of a hacky way to get
        # a black background which we still have control over, but it works, and performance is good
        self.black = OMXPlayer('black.mp4', dbus_name='org.mpris.MediaPlayer2.black', \
            args=['--no-osd', '--no-keys', '-b', '--end-paused', '--layer='+str(LAYER_UNMUTE)])

        # Set OMX players (None until a video is loaded)
        self.omxplayer_playing = None
        self.omxplayer_loaded = None
        self.omxplayer_loop = None

        # Variables tracking videos playing and loaded 
        self.playing_video_number = None
        self.loaded_video_number = None
        self.playing_video_path = None
        self.loaded_video_path = None
        self._is_looping = False
        self._loop_number = 0   # This toggles whenever a loop occurs, to ensure looping videos don't clash in dbus name
        self._check_end_thread = None

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
        # Check if there is also a seek command with the load
        seek = False
        if re.search(r'SE.*', msg_data):
            load_command = re.sub(r'SE.*', '', msg_data)
            seek = True
        else:
            # No seek command
            load_command = msg_data
        
        # Load the video
        load_return_code = self._load_video(load_command)

        if load_return_code == Load_Result.SUCCESS:
            # Are we also seeking when loading?
            if seek == True:
                # We are loading this file with a seek.
                # To do seek, we need to pass the video frames and duration. We use ffprobe to get
                # this info
                fps, duration = self._get_fps_duration_metadata(self.loaded_video_path)
                seek_timestamp = re.sub(r'.*SE', '', msg_data)
                seek_result, seek_time_secs = self._get_seek_time(seek_timestamp, fps, duration)

                if (seek_result == Seek_Result.SUCCESS) or (seek_result == Seek_Result.SUCCESS_FRAME_ERROR):
                    # Seek to correct position in the video
                    self.omxplayer_loaded.set_position(seek_time_secs)

                if seek_result == Seek_Result.SUCCESS:
                    return 'Load and seek success'
                elif seek_result == Seek_Result.SUCCESS_FRAME_ERROR:
                    return 'Load success. Seek success with frame seek error. Ignored ff for seek'
                elif seek_result == Seek_Result.BAD_FORM:
                    return 'Load success. Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
                elif seek_result == Seek_Result.BAD_MM:
                    return 'Load success. Seek failure: mm must be between 00 and 59'
                elif seek_result == Seek_Result.BAD_SS:
                    return 'Load success. Seek failure: ss must be between 00 and 59'
                elif seek_result == Seek_Result.BAD_FF:
                    fps, _ = self._get_fps_duration_metadata(self.loaded_video_path)
                    return 'Load success. Seek failure: ff must be between 00 and frame rate (' + str(fps) + ')'
                elif seek_result == Seek_Result.TOO_LONG:
                    return 'Load success. Seek failure: sent time is more than video duration'
            else:
                return 'Load success'

        elif load_return_code == Load_Result.NO_FILE:
            return 'Load failure: Could not find file'
        elif load_return_code == Load_Result.BAD_COMMAND:
            return 'Load failure: Incorrect file number sent'
        elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
            return 'Load: File already playing'
        return 'Load failure: Unknown'

    def play_command(self, msg_data):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing
        Will try load video if video number included"""
        print('Player: Play command')
        # Check if file number has been included
        new_video_loaded = True
        if msg_data != '':
            load_return_code = self._load_video(msg_data)
            if load_return_code == Load_Result.NO_FILE:
                return 'Play failure: Could not find file'
            elif load_return_code == Load_Result.BAD_COMMAND:
                return 'Play failure: Incorrect file number sent'
            elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
                new_video_loaded = False
                # If the video has finished, we go back to the start 
                if self.omxplayer_playing.playback_status() == 'Done':
                    self.omxplayer_playing.set_position(0)

        # No file number included. Check there is a file already loaded
        elif self.loaded_video_number == None:
            return 'Play failure: no file loaded'
        # Plain PL command. Play the current video
        else:
            new_video_loaded = False

        if new_video_loaded:
            # New video has been loaded. Switch the players
            self.omxplayer_loaded.set_layer(LAYER_PLAYING)

            if self.omxplayer_playing != None:
                self.omxplayer_playing.quit()
                self.omxplayer_playing = None

            self.omxplayer_playing = self.omxplayer_loaded
       
            self.playing_video_number = self.loaded_video_number
            self.playing_video_path = self.loaded_video_path
            self.loaded_video_number = None
            self.loaded_video_path = None

        self._is_looping = False  # Controls loop
        if self.omxplayer_loop != None:
            self.omxplayer_loop.quit()
            self.omxplayer_loop = None

        self.omxplayer_playing.play()

        return 'Play success'     

    def pause_command(self, msg_data):
        """Pause command sent to player. 
        Pauses video if playing"""
        print('Player: Pause command')
        if self.playing_video_number == None:
            return 'Pause failure: no file loaded'
        self.omxplayer_playing.pause()
        return 'Pause success' 

    def loop_command(self, msg_data):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing.
        Will try load video if video number included"""
        print('Player: Loop command')
        # Check if file number has been included
        new_video_loaded = True
        if msg_data != '':
            load_return_code = self._load_video(msg_data)
            if load_return_code == Load_Result.NO_FILE:
                return 'Loop failure: Could not find file'
            elif load_return_code == Load_Result.BAD_COMMAND:
                return 'Loop failure: Incorrect file number sent'
            elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
                new_video_loaded = False
                # If the video has finished, we go back to the start 
                if self.omxplayer_playing.playback_status() == 'Done':
                    self.omxplayer_playing.set_position(0)

        # No file number included. Check there is a file already loaded
        elif self.loaded_video_number == None:
            return 'Loop failure: no file loaded'
        # Plain LP command. Loop the current video
        else:
            new_video_loaded = False

        if new_video_loaded:
            # If we were looping the old video, kill the thread to check the end to die
            if self._is_looping == True:
                self._is_looping = False
                self._check_end_thread.join()

            # New video has been loaded. Switch the players and play
            self.omxplayer_loaded.set_layer(LAYER_PLAYING)

            if self.omxplayer_playing != None:
                self.omxplayer_playing.quit()
                self.omxplayer_playing = None
            if self.omxplayer_loop != None:
                self.omxplayer_loop.quit()
                self.omxplayer_loop = None
            
            self.omxplayer_playing = self.omxplayer_loaded

            self.playing_video_number = self.loaded_video_number
            self.playing_video_path = self.loaded_video_path
            self.loaded_video_number = None
            self.loaded_video_path = None

        # Play video
        self.omxplayer_playing.play()

        # Return if we're already looping
        if self._is_looping == True:
            return 'Loop success' 

        # Loads same video on the "loop layer". When the playing video stops, this will play instantly after
        self.omxplayer_loop = OMXPlayer(self.playing_video_path, dbus_name='org.mpris.MediaPlayer2.omxplayerfirstloop' \
            + str(self.playing_video_number), args=['--no-osd', '--no-keys', '-b', '--start-paused', '--end-paused', '--layer='+str(LAYER_LOOP)])

        # Start thread to check end of playing video
        self._is_looping = True
        self._check_end_thread = threading.Thread(target=self._check_end)
        self._check_end_thread.daemon = True
        self._check_end_thread.start()
        
        return 'Loop success' 

    def stop_command(self, msg_data):
        """Stop command sent to player.
        Stops playback, and clears playlist. 
        Essentially a quit without terminiating the player"""
        print('Player: Stop command')
        if self.playing_video_number == None:
            return 'Stop failure: no file loaded'
        self.omxplayer_playing.stop()
        return 'Stop success'

    def seek_command(self, msg_data):
        """Seek command sent to player.
        Seek to time passed in with message (in ms)"""
        print('Player: Seek command')
        if self.playing_video_number == None:
            return 'Seek failure: no file loaded'
        # Get seek time in seconds and result code
        fps, duration = self._get_fps_duration_metadata(self.playing_video_path)
        seek_result_code, seek_time_secs = self._get_seek_time(msg_data, fps, duration)
        # Check result of getting the seek time
        if seek_result_code == Seek_Result.SUCCESS:
            # Sikh
            self.omxplayer_playing.set_position(seek_time_secs)
            return 'Seek success'
        elif seek_result_code == Seek_Result.BAD_FORM:
            return 'Seek failure: incorrect seek time sent. Check time is in form hh:mm:ss:ff'
        elif seek_result_code == Seek_Result.BAD_MM:
            return 'Seek failure: mm must be between 00 and 59'
        elif seek_result_code == Seek_Result.BAD_SS:
            return 'Seek failure: ss must be between 00 and 59'
        elif seek_result_code == Seek_Result.BAD_FF:
            return 'Seek failure: ff must be between 00 and frame rate (' + str(fps) + ')'
        elif seek_result_code == Seek_Result.TOO_LONG:
            return 'Seek failure: sent time is more than video duration'
        elif seek_result_code == Seek_Result.SUCCESS_FRAME_ERROR:
            return 'Seek success with frame seek error. Ignored ff for seek'

    def video_mute_command(self, msg_data):
        """Video mute command sent to player.
        Will mute or unmute video depending on sent command"""
        print('Player: Video Mute command')
        mute_option = 0
        try:
            mute_option = int(msg_data)
        except Exception:
            return 'Video Mute error: incorrect or no option sent'
        # If we're unmuting
        if mute_option == 0:
            self.mpv_player.command('vf', 'set', '')
            return 'Video Mute success: video unmuted'
        # If we're muting
        elif mute_option == 1:
            self.mpv_player.command('vf', 'set', 'drawbox=x=0:y=0:w=1920:h=1080:color=black:t=fill') # TODO: using 1920x1080. Correct?
            # self.mpv_player.command('vf', 'set', 'drawbox=x=0:y=0:w=' + str(self.mpv_player.dwidth) + ':h=' + str(self.mpv_player.dheight) + ':color=black:t=fill')
            return 'Video Mute success: video muted'
        else:
            return 'Video Mute error: specify 0 for unmute and 1 for mute'

    def audio_mute_command(self, msg_data):
        """Audio mute command sent to player.
        Will mute or unmute audio depending on sent command"""
        print('Player: Audio Mute command')
        mute_option = 0
        try:
            mute_option = int(msg_data)
        except Exception:
            return 'Audio Mute error: incorrect or no option sent'
        # If we're unmuting
        if mute_option == 0:
            self.mpv_player.ao_mute = False
            return 'Audio Mute success: video unmuted'
        # If we're muting
        elif mute_option == 1:
            self.mpv_player.ao_mute = True
            return 'Audio Mute success: video muted'
        else:
            return 'Audio Mute error: specify 0 for unmute and 1 for mute'
           
    ################################################################################
    # Utility functions
    ################################################################################
    def quit(self, *args):
        """Shuts down player"""
        print('Player: Shutdown')
        if self.omxplayer_playing != None:
            self.omxplayer_playing.quit()
        if self.omxplayer_loaded != None:
            self.omxplayer_loaded.quit()
        if self.omxplayer_loop != None:
            self.omxplayer_loop.quit()
        # If there is a looping thread, kill it
        self._is_looping = False
        if self._check_end_thread != None: 
            self._check_end_thread.join() # wait for end of thread
        self.black.quit()

    def _load_video(self, command):
        """Tries to loads the video file number passed in"""       
        # Try to convert command into a video number. If can't, throw error
        try:
            video_number = int(command)
        except Exception as ex:
            print("Player: Load exception. Can't convert into number: " + str(ex))
            return Load_Result.BAD_COMMAND

        if video_number == self.playing_video_number:
            # Video already playing
            return Load_Result.FILE_ALREADY_PLAYING
        if video_number == self.loaded_video_number:
            # Video already loaded
            return Load_Result.SUCCESS

        # Search all correctly named video files for video number
        basepath = Path(self.video_folder)
        # Go through every file with 5 digits at the end of file name
        for video_file in basepath.glob('*[0-9][0-9][0-9][0-9][0-9].mp4'):
            # Extract number. Get number at end of file name, remove the file extension part, cast into an int
            file_number = int(re.findall(r'\d\d\d\d\d\.mp4', video_file.name)[0][0:5])
            # Check if we have a match
            if file_number == video_number:
                # We have a match
                # Load video. dbus name will be appended with the video number, so every new player will have unique dbus name
                self.omxplayer_loaded = OMXPlayer(str(video_file.resolve()), dbus_name='org.mpris.MediaPlayer2.omxplayer' \
                    + str(video_number), args=['--no-osd', '--no-keys', '-b', '--start-paused', '--end-paused', '--layer='+str(LAYER_LOADING)])
                # Keep track of loaded video
                self.loaded_video_number = video_number 
                self.loaded_video_path = str(video_file.resolve())
                       
                return Load_Result.SUCCESS

        return Load_Result.NO_FILE

    def _get_seek_time(self, seek_time, video_frames, video_duration):
        """Gets seek time passed in seconds. Returns result. Done this way because in the case of LD, 
        we may want to do a seek for a video that isn't this one"""
        seek_time = seek_time.strip()
        seek_time = seek_time.lstrip()
        # Check time stamp is correct format
        if not re.match(r'^\d\d:\d\d:\d\d:\d\d$', seek_time):
            return Seek_Result.BAD_FORM, 0
        
        timestamp_parts = seek_time.split(':')
       
        # Add hour seek time
        seek_hours = int(timestamp_parts[0])
        seek_time_secs = seek_hours * 3600
        
        # Add minutes seek time
        seek_mins = int(timestamp_parts[1])
        if seek_mins > 59:
             return Seek_Result.BAD_MM, 0
        seek_time_secs = seek_time_secs + (seek_mins * 60)
        
        # Add seconds seek time
        seek_seconds = int(timestamp_parts[2])
        if seek_seconds > 59:
             return Seek_Result.BAD_SS, 0
        seek_time_secs = seek_time_secs + (seek_seconds)
        
        # Add frame seek time
        seek_frames = int(timestamp_parts[3])
        frame_error = False
        
        if video_frames == 0:
            print('Seek: frame seek error. Ignoring ff for seek')
            frame_error = True        
        else:
            if seek_frames > video_frames:
                return Seek_Result.BAD_FF, 0
            else:
                seek_time_secs = seek_time_secs + ((1 / video_frames) * seek_frames)
        
        # Check if seek time is actually within the video duration 
        if seek_time_secs > video_duration:
            return Seek_Result.TOO_LONG, 0
       
        if frame_error:
            return Seek_Result.SUCCESS_FRAME_ERROR, seek_time_secs
        else:
            return Seek_Result.SUCCESS, seek_time_secs
        
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

    def _check_end(self): 
        """Will constantly poll currently playing media to check if it's stopped, or if we're no longer looping"""
        # Wrap in try except as it is possible for omxplayer to be closed, and thus raise an exception
        try:
            while (self.omxplayer_playing.playback_status() != 'Done') and (self._is_looping):
                time.sleep(0.01)
        except Exception as ex:
            # Playing omxplayer has been closed. Looping has been cancelled
            print('Exception in check end thread. Most likely playing omxplayer has been closed: ' + str(ex))
            return

        if self._is_looping == False:
            # If we're no longer looping, return
            return

        # Video has ended, we are now looping. Play same video and move to playing layer
        self.omxplayer_loop.set_layer(LAYER_PLAYING)
        self.omxplayer_loop.play()
        self.omxplayer_playing.quit()
        self.omxplayer_playing = None
        
        self.omxplayer_playing = self.omxplayer_loop
        self.omxplayer_loop = None
        
        # Reload same video on the "loop layer".
        self.omxplayer_loop = OMXPlayer(self.playing_video_path, dbus_name='org.mpris.MediaPlayer2.omxplayerloop' + str(self._loop_number) \
            + str(self.playing_video_number), args=['--no-osd', '--no-keys', '-b', '--start-paused', '--end-paused', '--layer='+str(LAYER_LOOP)])
        self._loop_number ^= 1 # Toggle loop number

        # Reset thread
        self._check_end_thread = threading.Thread(target=self._check_end)
        self._check_end_thread.daemon = True
        self._check_end_thread.start()