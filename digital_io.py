import gpiozero
from time import sleep
import configparser
import random
from mp2_details import config_path

# import debugpy

class DigitalIO():
    """The digital IO control for the player"""
    
    def __init__(self, player):
        """Initalise I/O"""
        self.player = player
        self.input_1 = gpiozero.Button(pin="GPIO20", pull_up=True)
        self.input_2 = gpiozero.Button(pin="GPIO21", pull_up=True)

        self.input_1.when_activated = self.input_1_active
        self.input_1.when_deactivated = self.input_1_inactive

        self.input_2.when_activated = self.input_2_active
        self.input_2.when_deactivated = self.input_2_inactive

    def do_action(self, action, track):
        """ Do player action depending on what is passed in"""
        if action == 'play':
            self.player.play_command(track)
        elif action == 'loop':
            self.player.loop_command(track)
        elif action == 'random':
            random_track = random.randint(1, int(track))
            self.player.play_command(str(random_track))
        elif action == 'stop':
            self.player.stop_command('')
        elif action == 'pause':
            self.player.pause_command('')
        elif action == 'audio_mute':
            self.player.audio_mute_command('1')
        elif action == 'video_mute':
            self.player.video_mute_command('1')
        elif action == 'audio_unmute':
            self.player.audio_mute_command('0')
        elif action == 'video_unmute':
            self.player.video_mute_command('0')
        
    def input_1_active(self):
        print("Digital I/O: Input 1 active")
        config = configparser.ConfigParser()
        config.read(config_path)
        input_action = config['MP2']['input1_on']
        input_track = config['MP2']['input1_on_track']

        self.do_action(input_action, input_track)

    def input_1_inactive(self):
        print("Digital I/O: Input 1 inactive")
        config = configparser.ConfigParser()
        config.read(config_path)
        input_action = config['MP2']['input1_off']
        input_track = config['MP2']['input1_off_track']

        self.do_action(input_action, input_track)

    def input_2_active(self):
        print("Digital I/O: Input 2 active")
        config = configparser.ConfigParser()
        config.read(config_path)
        input_action = config['MP2']['input2_on']
        input_track = config['MP2']['input2_on_track']

        self.do_action(input_action, input_track)

    def input_2_inactive(self):
        print("Digital I/O: Input 2 inactive")
        config = configparser.ConfigParser()
        config.read(config_path)
        input_action = config['MP2']['input2_off']
        input_track = config['MP2']['input2_off_track']

        self.do_action(input_action, input_track)
