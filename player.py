from tcp_server import PlayerTCPServer
from omxplayer.player import OMXPlayer
from mp2_details import config_path # pylint: disable=import-error
import storage

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
import threading
import configparser
import gpiozero

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
    FILE_LOAD_ERROR        = 5

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
        self.black = OMXPlayer('/home/pi/XTEC-PiPlayer/black.mp4', dbus_name='org.mpris.MediaPlayer2.omxplayerblack', \
            args=['--no-osd', '--no-keys', '-b', '--end-paused', '--layer='+str(LAYER_UNMUTE)])

        # Set OMX players (None until a video is loaded)
        self.omxplayer_playing = None
        self.omxplayer_loaded = None

        # Variables tracking videos playing and loaded 
        self.playing_video_number = None    # Playing video file number
        self.loaded_video_number = None     # Loaded video file number
        self.playing_video_path = None      # Playing video file path
        self.loaded_video_path = None       # Loaded video file path
        self.is_playing = False             # If we're currently playing something (i.e. not paused)
        self.is_looping = False             # If we're looping
        self._dbus_id = 0                   # Increments whenever a video is loaded, to ensure videos don't clash in dbus name
        self._check_end_thread = None       # Thread that is used for checking end of video
        
        # Events for anyone observing playing and not playing events
        self.playing_observers = []
        self.not_playing_observers = []
        # self.playing_event = Event()        # Playing event. Called when player starts playing
        # self.not_playing_event = Event()    # Not playing event. Called when player isn't playing. 

        # GPIO for DAC mute. Starts unmuted
        self.gpio_unmute = gpiozero.DigitalOutputDevice(pin="GPIO22", initial_value=True)
        # Setup operation status led outputs
        self.led_red = gpiozero.DigitalOutputDevice(pin="GPIO44", initial_value=False)
        self.led_green = gpiozero.DigitalOutputDevice(pin="GPIO45", initial_value=False)

        # Main folder where SD card is mounted, and where videos are stored
        self.video_folder = storage.SD_STORAGE_PATH

    ################################################################################
    # Player command functions
    ################################################################################
    def load_command(self, msg_data):
        """Load command sent to player.
        Loads video number sent to it. Can also be combined with seek command to seek 
        to specific position in loaded video."""
        print('Player: Load command')
        self.led_red.blink(on_time=0.1, off_time=0.1)
        self.led_green.off()
        return_code = ''
        seek = False
        # Check if there is also a seek command with the load
        if re.search(r'.*SE', msg_data):
            load_command = re.sub(r'.*SE', '', msg_data)
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
                seek_timestamp = re.sub(r'SE.*', '', msg_data)
                seek_result, seek_time_secs = self._get_seek_time(seek_timestamp, fps, duration)

                if (seek_result == Seek_Result.SUCCESS) or (seek_result == Seek_Result.SUCCESS_FRAME_ERROR):
                    # Seek to correct position in the video 
                    self.omxplayer_loaded.set_position(seek_time_secs)
                    time.sleep(0.1)
                    self.omxplayer_loaded.step()

                if seek_result == Seek_Result.SUCCESS:
                    return_code = 'OK1\r'
                elif seek_result == Seek_Result.SUCCESS_FRAME_ERROR:
                    return_code = 'OK2\r'
                elif seek_result == Seek_Result.BAD_FORM:
                    return_code = 'OK3\r'
                elif seek_result == Seek_Result.BAD_MM:
                    return_code = 'OK4\r'
                elif seek_result == Seek_Result.BAD_SS:
                    return_code = 'OK5\r'
                elif seek_result == Seek_Result.BAD_FF:
                    return_code = 'OK6\r'
                elif seek_result == Seek_Result.TOO_LONG:
                    return_code = 'OK7\r'
            else:
                return_code = 'OK1\r'

        elif load_return_code == Load_Result.NO_FILE:
            return_code = 'ER1\r'
        elif load_return_code == Load_Result.BAD_COMMAND:
            return_code = 'ER2\r'
        elif load_return_code == Load_Result.FILE_LOAD_ERROR:
            return_code = 'ER3\r'
        elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
            return_code = 'OK2\r'
        else:
            return_code = 'ER4\r'
        
        # Set status LED depending on operation and return the return code
        if re.match(r'OK', return_code):
            # Success. Turn on green led
            self.led_green.on()
            self.led_red.off()
        else:
            # Failure. Turn on red led
            self.led_red.on()

        return return_code

    def play_command(self, msg_data):
        """Play command sent to player. 
        Sets loop to false, and plays video if not already playing
        Will try load video if video number included"""
        print('Player: Play command')
        self.led_red.blink(on_time=0.1, off_time=0.1)
        self.led_green.off()
        return_code = ''
        # Check if file number has been included
        new_video_loaded = True
        if msg_data != '':
            load_return_code = self._load_video(msg_data)
            if load_return_code == Load_Result.NO_FILE:
                return_code = 'ER1\r'
            elif load_return_code == Load_Result.BAD_COMMAND:
                return_code = 'ER2\r'
            elif load_return_code == Load_Result.FILE_LOAD_ERROR:
                return_code = 'ER3\r'
            elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
                new_video_loaded = False
            elif load_return_code != Load_Result.SUCCESS:
                return_code = 'ER4\r'
            # If there's been an error
            if return_code != '':
                self.led_red.on()
                return return_code

        # No file number included. Check there is a file already playing
        elif self.omxplayer_playing != None:
            # If the video has finished, restart it
            if self.omxplayer_playing.is_done():
                self._load_video(self.playing_video_number)
            else:
                new_video_loaded = False

        # Check there is a file already loaded
        elif self.omxplayer_loaded != None:
            new_video_loaded = True

        # No file playing or loaded
        else:
            self.led_red.on()
            return 'ER5\r'

        if new_video_loaded:
            # New video has been loaded. Switch the players
            self._switch_loaded_to_playing()
            # Restart the thread to check for end of video
            self._restart_check_end()
            
        self.omxplayer_playing.play()

        self.is_playing = True
        self.is_looping = False
        self.omxplayer_playing.set_loop(False)
        self.led_red.off()
        self.led_green.on()

        # Notify observers we're playing
        for callback in self.playing_observers:
            callback(self)
            
        return 'OK1\r'     

    def loop_command(self, msg_data):
        """Loop command sent to player.
        Sets loop to true, and plays video if not already playing.
        Will try load video if video number included"""
        print('Player: Loop command')
        self.led_red.blink(on_time=0.1, off_time=0.1)
        self.led_green.off()
        return_code = ''
        # Check if file number has been included
        new_video_loaded = True
        if msg_data != '':
            load_return_code = self._load_video(msg_data)
            if load_return_code == Load_Result.NO_FILE:
                return_code = 'ER1\r'
            elif load_return_code == Load_Result.BAD_COMMAND:
                return_code = 'ER2\r'
            elif load_return_code == Load_Result.FILE_LOAD_ERROR:
                return_code = 'ER3\r'
            elif load_return_code == Load_Result.FILE_ALREADY_PLAYING:
                new_video_loaded = False
            elif load_return_code != Load_Result.SUCCESS:
                return_code = 'ER4\r'
            # If there's been an error
            if return_code != '':
                self.led_red.on()
                return return_code

        # No file number included. Check there is a file already playing
        elif self.omxplayer_playing != None:
            # If the video has finished, restart it
            if self.omxplayer_playing.is_done():
                self._load_video(self.playing_video_number)
            else:
                new_video_loaded = False

        # Check there is a file already loaded
        elif self.omxplayer_loaded != None:
            new_video_loaded = True

        # No file playing or loaded
        else:
            self.led_red.on()
            return 'ER5\r'

        if new_video_loaded:
            # New video has been loaded. Switch the players and play
            self._switch_loaded_to_playing()
            # Restart the thread to check for end of video
            self._restart_check_end()

        # Play video
        self.omxplayer_playing.play()
        self.is_looping = True
        self.is_playing = True
        self.omxplayer_playing.set_loop(True)
        self.led_red.off()
        self.led_green.on()

        # Notify observers we're playing
        for callback in self.playing_observers:
            callback(self)

        return 'OK1\r'

    def pause_command(self, msg_data):
        """Pause command sent to player. 
        Pauses video if playing"""
        print('Player: Pause command')
        if self.omxplayer_playing == None:
            return 'ER1\r'
        self.omxplayer_playing.pause()
        self.is_playing = False

        # Notify observers we're not playing
        for callback in self.not_playing_observers:
            callback(self)
        self.led_green.off()
        return 'OK1\r' 

    def stop_command(self, msg_data):
        """Stop command sent to player.
        Stops playback (which is same as quit)"""
        print('Player: Stop command')
        self.led_green.off()
        self.led_red.off()
        if self.omxplayer_playing == None:
            return 'ER1\r'
        if self.omxplayer_playing != None:
            self.omxplayer_playing.quit()
            self.omxplayer_playing = None
            self.playing_video_number = None

        self.is_playing = False
        # Notify observers we're not playing
        for callback in self.not_playing_observers:
            callback(self)

        return 'OK1\r'

    def seek_command(self, msg_data):
        """Seek command sent to player.
        Seek to time passed in with message (in ms)"""
        print('Player: Seek command')
        if self.omxplayer_playing == None:
            return 'ER6\r'
        # Get seek time in seconds and result code
        fps, duration = self._get_fps_duration_metadata(self.playing_video_path)
        seek_result_code, seek_time_secs = self._get_seek_time(msg_data, fps, duration)
        # Check result of getting the seek time
        if (seek_result_code == Seek_Result.SUCCESS) or (seek_result_code == Seek_Result.SUCCESS_FRAME_ERROR):
            # Sikh
            self.omxplayer_playing.set_position(seek_time_secs)
            time.sleep(0.1)
            self.omxplayer_playing.step()
        if seek_result_code == Seek_Result.SUCCESS:
            return 'OK1\r'
        elif seek_result_code == Seek_Result.SUCCESS_FRAME_ERROR:
            return 'OK2\r'
        elif seek_result_code == Seek_Result.BAD_FORM:
            return 'ER1\r'
        elif seek_result_code == Seek_Result.BAD_MM:
            return 'ER2\r'
        elif seek_result_code == Seek_Result.BAD_SS:
            return 'ER3\r'
        elif seek_result_code == Seek_Result.BAD_FF:
            return 'ER4\r'
        elif seek_result_code == Seek_Result.TOO_LONG:
            return 'ER5\r'

    def video_mute_command(self, msg_data):
        """Video mute command sent to player.
        Will mute or unmute video depending on sent command"""
        print('Player: Video Mute command')
        mute_option = 0
        try:
            mute_option = int(msg_data)
        except Exception:
            return 'ER1\r'
        # If we're unmuting
        if mute_option == 0:
            self.black.set_layer(LAYER_UNMUTE)
            return 'OK1\r'
        # If we're muting
        elif mute_option == 1:
            self.black.set_layer(LAYER_MUTE)
            return 'OK2\r'
        else:
            return 'ER2\r'

    def audio_mute_command(self, msg_data):
        """Audio mute command sent to player.
        Will mute or unmute audio with GPIO connection to DAC depending on sent command"""
        print('Player: Audio Mute command')
        mute_option = 0
        try:
            mute_option = int(msg_data)
        except Exception:
            return 'ER1\r'
        # If we're unmuting
        if mute_option == 0:
            self.gpio_unmute.on()
            return 'OK1\r'
        # If we're muting
        elif mute_option == 1:
            self.gpio_unmute.off()
            return 'OK2\r'
        else:
            return 'ER2\r'
           
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
        if self._check_end_thread != None: 
            self._check_end_thread.join() # wait for check end thread
        self.black.quit()

    def bind_to_playing(self, callback):
        """Binds a callback to the playing event"""
        self.playing_observers.append(callback)
    
    def bind_to_not_playing(self, callback):
        """Binds a callback to the not playing event"""
        self.not_playing_observers.append(callback)

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
            if not self.omxplayer_playing.is_done():
                return Load_Result.FILE_ALREADY_PLAYING
        elif video_number == self.loaded_video_number:
            # Video already loaded
            return Load_Result.SUCCESS

        # Search in video folder
        basepath = Path(self.video_folder)
        
        # Go through every file with 5 digits at the end of file name
        for video_file in basepath.glob('*[0-9][0-9][0-9][0-9][0-9].*'):
            # Extract number. Get number at end of file name, remove the file extension part, cast into an int
            file_number = int(re.findall(r'\d\d\d\d\d\.', video_file.name)[0][0:5])
            # Check if we have a match
            if file_number == video_number:
                # We have a match
                # Quit different loaded video if there is one
                if self.omxplayer_loaded != None:
                    self.omxplayer_loaded.quit()
                    self.omxplayer_loaded = None

                try:
                    # Get audio setting
                    config = configparser.ConfigParser()
                    config.read(config_path)
                    audio = config['MP2']['audio']
                    # Load video. dbus name will be appended with the video number, so every new player will have unique dbus name
                    arguments = ['-g', '--no-osd', '--no-keys', '--start-paused', '--end-paused', '--layer='+str(LAYER_LOADING), '--adev='+audio]
                    self.omxplayer_loaded = OMXPlayer(str(video_file.resolve()), \
                        dbus_name='org.mpris.MediaPlayer2.omxplayer' + str(video_number) + '_' + str(self._dbus_id), \
                        args=arguments)
                    # This checks if the player has been correctly loaded. Will raise exception if error
                    self.omxplayer_loaded.can_play() 
                    self._dbus_id += 1 # Increment dbus id

                except Exception as ex:
                    # Issue loading. Most likely incorrect file
                    print('Load: error loading file. Most likely incorrect file format: ' + str(ex))
                    self.omxplayer_loaded = None
                    return Load_Result.FILE_LOAD_ERROR

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
        
        if (video_frames == 0) or (video_frames == None):
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
        # try get fps and duration
        fps = 0
        duration = 0
        try:
            cmd = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1"
            args = shlex.split(cmd)
            args.append(videopath)
            # run the ffprobe process, decode stdout into utf-8
            duration = float(subprocess.check_output(args).decode('utf-8'))
            # Get information from final element in probe output
            cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=noprint_wrappers=1:nokey=1"
            args = shlex.split(cmd)
            args.append(videopath)
            aeval = Interpreter()
            fps = aeval(subprocess.check_output(args).decode('utf-8'))
        except Exception as ex:
            print('Error getting metadata: ' + str(ex))

        return fps, duration

    def _check_end(self): 
        """Will constantly poll currently playing media to check if it's stopped"""
        while True:
            # Wrap in try except as it is possible for omxplayer to be closed, and thus raise an exception
            try:
                while (self.omxplayer_playing.is_done() != True):
                    time.sleep(0.1)
                    pass
                
                self.is_playing = False
                self.led_green.off()
                self.led_red.off()
                # Notify observers we're not playing
                for callback in self.not_playing_observers:
                    callback(self)
                return

            except Exception as ex:
                # Playing omxplayer has been closed
                print('Exception in check end thread. Most likely playing omxplayer has been closed: ' + str(ex))
                return

    def _restart_check_end(self):
        """Restarts the check for end thread"""
        # Wait for old thread to exit
        if self._check_end_thread != None:
            while self._check_end_thread.is_alive():
                pass
        # Start thread to check end of playing video
        self._check_end_thread = threading.Thread(target=self._check_end, daemon=True)
        self._check_end_thread.start()

    def _switch_loaded_to_playing(self):
        """Puts loaded player to top layer"""
        self.omxplayer_loaded.set_layer(LAYER_LOOP)
        
        if self.omxplayer_playing != None:
            self.omxplayer_playing.stop()
            self.omxplayer_playing.quit()
            self._check_end_thread.join()     
            self.omxplayer_playing = None

        # When moving to playing layer, it automatically plays the video in omx
        self.omxplayer_loaded.set_layer(LAYER_PLAYING)
       
        self.omxplayer_playing = self.omxplayer_loaded
        self.omxplayer_loaded = None

        self.playing_video_number = self.loaded_video_number
        self.playing_video_path = self.loaded_video_path
        self.loaded_video_number = None
        self.loaded_video_path = None
