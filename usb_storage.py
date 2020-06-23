from pyudev import Context, Monitor, MonitorObserver
import os
import time
import re

usb_storage_path = 'usb_mount'

# Globals for the device details
USBDEV_UUID = None
USBDEV_VENDOR = None
USBDEV_SERID = None
USBDEV_FSTYPE = None
USBDEV_MODEL = None
USBDEV_DEVPATH = None
USBDEV_FILEPATH = None
USBDEV_CONNECTED = False

def usb_event_callback(action, device):
    """Callback when a usb device is plugged in"""
    global USBDEV_UUID
    global USBDEV_VENDOR
    global USBDEV_SERID
    global USBDEV_FSTYPE
    global USBDEV_MODEL
    global USBDEV_DEVPATH
    global USBDEV_FILEPATH
    global USBDEV_CONNECTED

    if action == 'add':
        usb_add(device)

    elif action == 'remove':
        print('Usb storage: usb remove')
        if USBDEV_CONNECTED:    
            # Clear the device data
            USBDEV_VENDOR = None
            USBDEV_SERID = None
            USBDEV_UUID = None
            USBDEV_FSTYPE = None
            USBDEV_MODEL = None
            USBDEV_DEVPATH = None
            USBDEV_CONNECTED = False

            try:
                # Unmount the dev path to the folder
                os.system("sudo umount " + USBDEV_FILEPATH)
                os.system("sudo mount " + USBDEV_DEVPATH + " " + usb_storage_path)
                USBDEV_FILEPATH = None

            except Exception as ex:
                print('Usb storage: Error unmounting usb: ' + str(ex))


def start_listener():
    """Create a context, create monitor at kernel level, select devices"""
    context = Context()
    monitor = Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')

    observer = MonitorObserver(monitor, usb_event_callback, name="usbdev")
    observer.start()

    # Check if there is already a usb attached
    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        if re.search('/dev/s.+', device.get('DEVNAME')):
            usb_add(device)
            continue

def get_device_data():
    """Returns usb device details"""
    if USBDEV_FILEPATH != None:
        global USBDEV_UUID
        global USBDEV_VENDOR
        global USBDEV_SERID
        global USBDEV_FSTYPE
        global USBDEV_MODEL
        global USBDEV_DEVPATH
        return {'UUID': USBDEV_UUID,
               'SERID': USBDEV_SERID, 
               'VENDOR': USBDEV_VENDOR, 
               'FSTYPE': USBDEV_FSTYPE,
               'MODEL': USBDEV_MODEL,
               'DEVPATH': USBDEV_DEVPATH}
    return None

def usb_add(device):
    """Mounts the usb to a local filesystem"""
    global USBDEV_UUID
    global USBDEV_VENDOR
    global USBDEV_SERID
    global USBDEV_FSTYPE
    global USBDEV_MODEL
    global USBDEV_DEVPATH
    global USBDEV_FILEPATH
    global USBDEV_CONNECTED

    print('Usb storage: usb add')
    # Store the device values
    USBDEV_VENDOR = device.get('ID_VENDOR')
    USBDEV_SERID = device.get('ID_SERIAL')
    USBDEV_UUID = device.get('ID_FS_UUID')
    USBDEV_FSTYPE = device.get('ID_FS_TYPE')
    USBDEV_MODEL = device.get('ID_MODEL')
    USBDEV_DEVPATH = device.get('DEVNAME')
    USBDEV_CONNECTED = True

    # Check if the dev path exists
    if os.path.exists(USBDEV_DEVPATH):

        # Create a mount directory
        if not os.path.exists(usb_storage_path):
            os.makedirs(usb_storage_path)

        try:
            # Mount the dev path to the folder
            os.system("sudo mount " + USBDEV_DEVPATH + " " + usb_storage_path)
            # Return the path to the folder from root
            USBDEV_FILEPATH = os.getcwd() + '/' + usb_storage_path

        except Exception as ex:
            print('Usb storage: Error mounting usb: ' + str(ex))