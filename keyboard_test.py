import keyboard
from pyudev import Context, Monitor, MonitorObserver
import time
import importlib
from evdev import InputDevice, categorize, ecodes
import threading


def usb_event_callback(action, device):
    """Callback when a usb device is plugged in"""

    if (action == 'add') and (device.get('ID_INPUT_KEYBOARD') == '1'):
        print('Keyboard: input add')
        if device.get('DEVNAME') != None:
            device = InputDevice(device.get('DEVNAME'))
            loop.run_until_complete(keyboard_event(device))


    elif (action == 'remove') and (device.get('ID_INPUT_KEYBOARD') == '1'):
        print('Keyboard: input remove')
            
# def key_input(key_pressed):
#     """Handles keyboard release"""
#     print('Keyboard Control: Key released: ' + key_pressed.name)
#     if key_pressed.name == 'space':
#         print('shit')

async def keyboard_event(device):
    try:
        async for event in device.async_read_loop():
            if event.type == ecodes.EV_KEY:
                print(ecodes.KEY[event.code])

    except Exception as ex:
        print('bum: ' + str(ex))


loop = asyncio.get_event_loop()

# Create a context, create monitor at kernel level, select devices
context = Context()
monitor = Monitor.from_netlink(context)
monitor.filter_by(subsystem='input')

observer = MonitorObserver(monitor, usb_event_callback, name="keyboard")
observer.start()

while 1:
    time.sleep(10)