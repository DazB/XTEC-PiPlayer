import gpiozero
import configparser
import oled
from mp2_details import config_path
import enum

class Page(enum.Enum): 
    """Page numbers"""
    FRONT                = 1
    MENU                 = 2

class UI:
    """The UI control for the player"""
    
    def __init__(self, player):
        """Initalise UI"""
        self.player = player
        # Setup button inputs
        self.input_up = gpiozero.DigitalInputDevice(pin="GPIO40", pull_up=True)
        self.input_down = gpiozero.DigitalInputDevice(pin="GPIO41", pull_up=True)
        self.input_enter = gpiozero.DigitalInputDevice(pin="GPIO42", pull_up=True)
        
        # Setup internal state
        self.page = Page.FRONT

        self.player.bind_to_playing(self.player_playing_event)           # Player "playing" callback 
        self.player.bind_to_not_playing(self.player_not_playing_event)   # Player "not playing" callback 
        

    def player_playing_event(self, player):
        """Event handler for whenever the player starts playing"""
        pass
        
    def player_not_playing_event(self, player):
        """Event handler for whenever the player stops playing"""
        pass