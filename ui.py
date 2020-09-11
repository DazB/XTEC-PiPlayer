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
        # Event callbacks
        self.player.bind_to_playing(self.player_playing_event)           # Player "playing" callback 
        self.player.bind_to_not_playing(self.player_not_playing_event)   # Player "not playing" callback 
        
        # Init screen
        oled.clear_DDRAM()
        oled.set_DDRAM_addr(0x00)
        oled.write_string_DDRAM('NOTHING PLAYING')

    def player_playing_event(self, player):
        """Event handler for whenever the player starts playing"""
        if self.page == Page.FRONT:
            oled.clear_DDRAM()
            oled.set_DDRAM_addr(0x00)
            if player.is_looping:
                oled.write_string_DDRAM('LOOPING')
            else:
                oled.write_string_DDRAM('PLAYING')
            
            oled.set_DDRAM_addr(0x40)
            file_name = player.playing_video_path.upper().split('/')[-1]
            if len(file_name) > oled.DDRAM_LINE_SIZE:
                oled.write_string_DDRAM(file_name[:oled.DDRAM_LINE_SIZE])
            else:
                oled.write_string_DDRAM(file_name)
        
    def player_not_playing_event(self, player):
        """Event handler for whenever the player stops playing"""
        if self.page == Page.FRONT:
            # If paused (Stop deletes player)
            if player.omxplayer_playing != None:
                oled.clear_top_DDRAM()
                oled.set_DDRAM_addr(0x00)
                oled.write_string_DDRAM('PAUSED')
            # Player stopped
            else:
                oled.clear_DDRAM()
                oled.set_DDRAM_addr(0x00)
                oled.write_string_DDRAM('NOTHING PLAYING')
