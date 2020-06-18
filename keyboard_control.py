import keyboard

class KeyboardControl:
    """The keyboard control for the player"""

    def __init__(self, player):
        self.player = player
        # Set up release handler
        keyboard.on_release(self.key_input)

    def key_input(self, key_pressed):
        """Handles keyboard release"""
        if key_pressed.name == 'space':
            if self.player.is_playing:
                self.player.pause_command('')
            else:
                self.player.play_command('')
        elif key_pressed.name == 'l':
            self.player.loop_command('')
        elif key_pressed.name == 'z':
            self.player.stop_command('')
        elif key_pressed.name == 'x':
            self.player.video_mute_command('1')
        elif key_pressed.name == 'c':
            self.player.video_mute_command('0')
        elif key_pressed.name == 'v':
            self.player.audio_mute_command('1')
        elif key_pressed.name == 'b':
            self.player.audio_mute_command('0')
        elif key_pressed.name == 's':
            self.player.stop_command('')
