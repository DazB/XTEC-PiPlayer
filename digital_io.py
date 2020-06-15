import gpiozero
from time import sleep
import configparser
import random
from mp2_details import config_path

import debugpy

class DigitalIO():
    """The digital IO control for the player"""
    
    def __init__(self, player):
        """Initalise I/O"""
        self.player = player
        self.input_1 = gpiozero.DigitalInputDevice(pin="GPIO20", pull_up=True)
        self.input_2 = gpiozero.DigitalInputDevice(pin="GPIO21", pull_up=True)
        self.input_1.when_activated = self.input_1_active
        self.input_1.when_deactivated = self.input_1_inactive
        self.input_2.when_activated = self.input_2_active
        self.input_2.when_deactivated = self.input_2_inactive

        self.output_1 = gpiozero.DigitalOutputDevice(pin="GPIO2")
        self.output_2 = gpiozero.DigitalOutputDevice(pin="GPIO3")
        self.player.playing_event = self.player_playing_event           # Player "playing" callback 
        self.player.not_playing_event = self.player_not_playing_event   # Player "not playing" callback 

        # Check boot options
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            if config['MP2']['output1'] == 'on_boot':
                self.output_1.on()
            if config['MP2']['output1'] == 'pulse_boot':
                self.output_1.blink()
            if config['MP2']['output2'] == 'on_boot':
                self.output_2.on()
            if config['MP2']['output2'] == 'pulse_boot':
                self.output_2.blink()

        except Exception as ex:
            print('Digital I/O: Player play error: ' + str(ex))      

    ############################################################################
    # Inputs
    ############################################################################
    def input_1_active(self):
        print("Digital I/O: Input 1 active")
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            self.do_input_action(config['MP2']['input1_on'], config['MP2']['input1_on_track'], config['MP2']['input1_on_ignore'])

        except Exception as ex:
            print('Digital I/O: Input 1 active error: ' + str(ex))


    def input_1_inactive(self):
        print("Digital I/O: Input 1 inactive")
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            self.do_input_action(config['MP2']['input1_off'], config['MP2']['input1_off_track'], config['MP2']['input1_off_ignore'])

        except Exception as ex:
            print('Digital I/O: Input 1 inactive error: ' + str(ex))

    def input_2_active(self):
        print("Digital I/O: Input 2 active")
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            self.do_input_action(config['MP2']['input2_on'], config['MP2']['input2_on_track'], config['MP2']['input2_on_ignore'])

        except Exception as ex:
            print('Digital I/O: Input 2 active error: ' + str(ex))

    def input_2_inactive(self):
        print("Digital I/O: Input 2 inactive")
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            self.do_input_action(config['MP2']['input2_off'], config['MP2']['input2_off_track'], config['MP2']['input2_off_ignore'])

        except Exception as ex:
            print('Digital I/O: Input 2 inactive error: ' + str(ex))

    def do_input_action(self, action, track, ignore):
        """Do player action depending on what is passed in"""
        # Check if we ignore this input
        if ignore == '1':
            # If we're currently playing back and it isn't track 0
            if self.player.is_playing and str(self.player.playing_video_number) != '0':
                # We ignore this input
                return
        # Else we check what action to take on this input change
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

    ############################################################################
    # Outputs
    ############################################################################
    def player_playing_event(self, player):
        """Event handler for whenever the player starts playing"""
        try:
            debugpy.breakpoint()
            config = configparser.ConfigParser()
            config.read(config_path)
            self.do_output_action(config['MP2']['output1'], config['MP2']['output1_track'], self.output_1)
            self.do_output_action(config['MP2']['output2'], config['MP2']['output2_track'], self.output_2)

        except Exception as ex:
            print('Digital I/O: Player play error: ' + str(ex))      
        
    def player_not_playing_event(self, player):
        """Event handler for whenever the player stops playing"""
        try:
            # We turn off the outputs when the player stops playing, unless they are related to
            # booting
            config = configparser.ConfigParser()
            config.read(config_path)
            if config['MP2']['output1'] != 'on_boot' or config['MP2']['output1'] != 'pulse_boot':
                self.output_1.off()
            if config['MP2']['output2'] != 'on_boot' or config['MP2']['output2'] != 'pulse_boot':
                self.output_2.off()
        except Exception as ex:
            print('Digital I/O: Player not play error: ' + str(ex))      

    def do_output_action(self, action, track, output):
        """Change outputs depending on what is passed in"""
        if action == 'on_playing':
            output.on()
        elif action == 'pulse_playing':
            output.blink()
        elif action == 'on_track' and track == str(self.player.playing_video_number):
            output.on()
        elif action == 'pulse_track' and track == str(self.player.playing_video_number):
            output.blink()