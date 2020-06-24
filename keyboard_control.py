from pyudev import Context, Monitor, MonitorObserver, Devices
from evdev import InputDevice, categorize, ecodes
import threading
import time

class KeyboardControl:
    """The keyboard control for the player"""

    def __init__(self, player):
        try:
            self.player = player
            
             # Create a context, create monitor at kernel level, select devices
            context = Context()
            monitor = Monitor.from_netlink(context)
            monitor.filter_by(subsystem='input')

            self.observer = MonitorObserver(monitor, self.usb_event_callback, name="keyboard")
            self.observer.start()

            self.pressed = False    # Stores state of press
            
            # Check if there is already a keyboard attached
            for device in context.list_devices(subsystem='input'):
                if device.get('ID_INPUT_KEYBOARD') == '1':
                    if device.get('DEVNAME') != None:
                        device_name = InputDevice(device.get('DEVNAME'))
                        thread = threading.Thread(target=self.keyboard_event, args=(device_name,), daemon=True)
                        thread.start()
                        continue


        except Exception as ex:
            print('Keyboard Control: Error starting: ' + str(ex))

    def usb_event_callback(self, action, device):
        """Callback when a usb device is plugged in"""
        if action == 'add' and device.get('ID_INPUT_KEYBOARD') == '1':
            print('Keyboard: input add')
            if device.get('DEVNAME') != None:
                device_name = InputDevice(device.get('DEVNAME'))
                thread = threading.Thread(target=self.keyboard_event, args=(device_name,), daemon=True)
                thread.start()
            
    def key_input(self, key_pressed):
        print('Keyboard Control: Key pressed: ' + key_pressed)
        if key_pressed == 'KEY_SPACE':
            if self.player.is_playing:
                self.player.pause_command('')
            else:
                self.player.play_command('')
        elif key_pressed == 'KEY_L':
            self.player.loop_command('')
        elif key_pressed == 'KEY_Z':
            self.player.stop_command('')
        elif key_pressed == 'KEY_X':
            self.player.video_mute_command('1')
        elif key_pressed == 'KEY_C':
            self.player.video_mute_command('0')
        elif key_pressed == 'KEY_V':
            self.player.audio_mute_command('1')
        elif key_pressed == 'KEY_B':
            self.player.audio_mute_command('0')
        elif key_pressed == 'KEY_S':
            self.player.stop_command('')

    def keyboard_event(self, device):
        """Handles keyboard events"""
        try:
            for event in device.read_loop():
                # This is a key press
                if event.type == ecodes.EV_KEY: # pylint: disable=no-member
                    # It is a press down
                    if event.value == 1:
                        # This is the first press we've seen
                        if self.pressed != True:
                            self.pressed = True
                            self.key_input(ecodes.KEY[event.code]) # pylint: disable=no-member
                    # Key released
                    elif event.value == 0:
                        self.pressed = False

        except Exception as ex:
            print('Keyboard control: Event error (most likely unplugged)' + str(ex))