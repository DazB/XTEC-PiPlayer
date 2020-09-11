import gpiozero
import configparser
import oled
from mp2_details import config_path
import enum
from threading import Timer

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
        # Player event callbacks
        self.player.bind_to_playing(self.player_playing_event)           # Player "playing" callback 
        self.player.bind_to_not_playing(self.player_not_playing_event)   # Player "not playing" callback 
        
        # Front page variables
        self.file_name = ''
        self.file_scroll = 0
        self.scroll_timer = None

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
            self.file_name = player.playing_video_path.upper().split('/')[-1]
            # Shorten name if too long
            if len(self.file_name) > oled.DDRAM_LINE_SIZE:
                self.file_name = self.file_name[:oled.DDRAM_LINE_SIZE]
            # Write file name to screen
            oled.write_string_DDRAM(self.file_name)
            # If file longer than display, start the scroll callback timer
            if len(self.file_name) > oled.OLED_DISPLAY_LINE_SIZE:
                self.scroll_timer = Timer(2, self.file_name_scroll_callback)
                self.scroll_timer.daemon = True
                self.scroll_timer.start()
        
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
                self.scroll_timer.cancel()

    def file_name_scroll_callback(self):
        """This callback function will scroll the playing file name on the front page"""
        oled.set_DDRAM_addr(0x40)
        if self.file_scroll < (len(self.file_name) - oled.OLED_DISPLAY_LINE_SIZE + 2):
            self.file_scroll += 1
            oled.clear_bot_DDRAM()
            oled.write_string_DDRAM(self.file_name[self.file_scroll: ])
            self.scroll_timer = Timer(1, self.file_name_scroll_callback)
        else:
            self.file_scroll = 0
            oled.clear_bot_DDRAM()
            oled.write_string_DDRAM(self.file_name[self.file_scroll: ])
            self.scroll_timer = Timer(4, self.file_name_scroll_callback)

        self.scroll_timer.daemon = True
        self.scroll_timer.start()

