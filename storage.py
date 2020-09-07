from pyudev import Context, Monitor, MonitorObserver
import os
import time
import re
import shutil

# Globals for the path details
SD_STORAGE_PATH = 'storage/sd_mount'
USB_STORAGE_PATH = 'storage/usb_mount'

class Storage:
    """Storage class. Used as an interface to the USB and SD card storage"""

    def __init__(self):
        """Create an instance of the SD and USB storage interface"""
        print("Storage: Creating instance")
        # USB device details
        self.USBDEV_UUID = None
        self.USBDEV_VENDOR = None
        self.USBDEV_SERID = None
        self.USBDEV_FSTYPE = None
        self.USBDEV_MODEL = None
        self.USBDEV_DEVPATH = None
        self.USBDEV_FILEPATH = None
        self.USBDEV_CONNECTED = False

        # SD device details
        self.SDDEV_UUID = None
        self.SDDEV_VENDOR = None
        self.SDDEV_SERID = None
        self.SDDEV_FSTYPE = None
        self.SDDEV_MODEL = None
        self.SDDEV_DEVPATH = None
        self.SDDEV_FILEPATH = None
        self.SDDEV_CONNECTED = False

        # Start the listener thread to check for new USB's and SD's
        self.start_listener()

    def start_listener(self):
        """Create a context, create monitor at kernel level, select devices"""
        context = Context()
        monitor = Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')

        observer = MonitorObserver(monitor, self.event_callback, name="storage_monitor")
        observer.start()
        
        # Check if there is already a usb attached
        for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
            if re.search('/dev/s.+', device.get('DEVNAME')):
                self.usb_add(device)
                continue
        
        # Check if there is already an sd attached
        for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
            if re.search('/dev/mmcblk1p1', device.get('DEVNAME')):
                self.sd_add(device)
                continue

    def event_callback(self, action, device):
        """Callback when a storage device is plugged in or out"""
        # If USB
        if re.search('/dev/s.+', device.get('DEVNAME')):
            if action == 'add':
                self.usb_add(device)

            elif action == 'remove':
                self.usb_remove()
        # If SD
        if re.search('/dev/mmcblk1p1', device.get('DEVNAME')):
            if action == 'add':
                self.sd_add(device)

            elif action == 'remove':
                self.sd_remove()

    def usb_add(self, device):
        """Mounts the usb to a local filesystem"""

        print('Storage: usb add')
        # Store the device values
        self.USBDEV_VENDOR = device.get('ID_VENDOR')
        self.USBDEV_SERID = device.get('ID_SERIAL')
        self.USBDEV_UUID = device.get('ID_FS_UUID')
        self.USBDEV_FSTYPE = device.get('ID_FS_TYPE')
        self.USBDEV_MODEL = device.get('ID_MODEL')
        self.USBDEV_DEVPATH = device.get('DEVNAME')
        self.USBDEV_CONNECTED = True

        # Check if the dev path exists
        if os.path.exists(self.USBDEV_DEVPATH):

            # Create a mount directory
            if not os.path.exists(USB_STORAGE_PATH):
                os.makedirs(USB_STORAGE_PATH)

            try:
                # Mount the dev path to the folder
                os.system("sudo mount " + self.USBDEV_DEVPATH + " " + USB_STORAGE_PATH)
                # Return the path to the folder from root
                self.USBDEV_FILEPATH = os.getcwd() + '/' + USB_STORAGE_PATH

            except Exception as ex:
                print('Storage: Error mounting usb: ' + str(ex))

    def usb_remove(self):
        """Unmounts USB from local filesystem"""
        print('Storage: usb remove')
        self.USBDEV_CONNECTED = False
        try:
            # Unmount the dev path to the folder
            os.system("sudo umount " + self.USBDEV_DEVPATH)
            shutil.rmtree(self.USBDEV_FILEPATH)

        except Exception as ex:
            print('Storage: Error unmounting usb: ' + str(ex))

    def sd_add(self, device):
        """Mounts the sd to a local filesystem"""

        print('Storage: sd add')
        # Store the device values
        self.SDDEV_VENDOR = device.get('ID_VENDOR')
        self.SDDEV_SERID = device.get('ID_SERIAL')
        self.SDDEV_UUID = device.get('ID_FS_UUID')
        self.SDDEV_FSTYPE = device.get('ID_FS_TYPE')
        self.SDDEV_MODEL = device.get('ID_MODEL')
        self.SDDEV_DEVPATH = device.get('DEVNAME')
        self.SDDEV_CONNECTED = True

        # Check if the dev path exists
        if os.path.exists(self.SDDEV_DEVPATH):

            # Create a mount directory
            if not os.path.exists(SD_STORAGE_PATH):
                os.makedirs(SD_STORAGE_PATH)

            try:
                # Mount the dev path to the folder
                os.system("sudo mount " + self.SDDEV_DEVPATH + " " + SD_STORAGE_PATH)
                # Return the path to the folder from root
                self.SDDEV_FILEPATH = os.getcwd() + '/' + SD_STORAGE_PATH

            except Exception as ex:
                print('Storage: Error mounting sd: ' + str(ex))

    def sd_remove(self):
        """Unmounts SD card from local filesystem"""
        print('Storage: sd remove')
        self.SDDEV_CONNECTED = False
        try:
            # Unmount the dev path to the folder
            os.system("sudo umount " + self.SDDEV_DEVPATH)
            shutil.rmtree(self.SDDEV_FILEPATH)

        except Exception as ex:
            print('Storage: Error unmounting sd: ' + str(ex))
