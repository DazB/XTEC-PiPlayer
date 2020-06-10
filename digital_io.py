import gpiozero
from time import sleep
import threading
import configparser
from mp2_details import config_path

class DigitalIO():
    """The digital IO control for the player"""
    
    def __init__(self, player):
        """Initalise IO"""
        self.player = player
        self.input_1 = gpiozero.Button(pin="GPIO20", pull_up=True)
        self.input_2 = gpiozero.Button(pin="GPIO21", pull_up=True)

        self.input_1.when_activated = self.input_1_active

    def input_1_active(self):
        config = configparser.ConfigParser()
        config.read(config_path)


        pass

