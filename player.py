#!/usr/bin/env python3

#######################################
## Pi Player
#######################################

from omxplayer.player import OMXPlayer
from pathlib import Path
import socket
import threading
import socketserver
import sys
from time import sleep
import signal

class Player:
    """Main video player class"""

    def __init__(self):
        """Create an instance of the main video player application class"""
        self.path = "/opt/vc/src/hello_pi/hello_video/test.h264" # Test file
        self.player = OMXPlayer(self.path, dbus_name='org.mpris.MediaPlayer2.omxplayer1', 
            pause=True, args=['--no-osd', '--no-keys', '-b'])

    def run(self):
        """Main program loop"""
        pass

    def play(self):
        """Main program loop"""
        print('Player play')
        self.player.play()

    def quit(self):
        """Shut down program"""
        self.player.quit()
        print('Player Shutdown')

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """TCP Request Handler class"""

    def __init__(self, request, client_address, server):
        # Dictionary of commands
        self.command_dict = {
            b'PL': player.play
        }
        # Extends StreamRequestHandler
        super().__init__(request, client_address, server)

    def handle(self):
        self.data = self.rfile.readline().strip()   # Get data
        
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)

        command = self.data[0:2]
        command_func = self.command_dict.get(command, self.unknown_command)
        command_func()

    def unknown_command(self):
        print('Unknown command')

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP Server Class"""

    # Allow address to be reused (i.e. reopen after unexpected close)
    allow_reuse_address = True  

    def quit(self):
        """Cleanup TCP server"""
        self.shutdown()
        self.server_close()
        print('TCP Shutdown')


def cleanup(signum, frame):
    """Cleanup function. Calls cleanup functions in each class"""
    print('Cleaning up')
    tcp_server.quit()
    player.quit()
    sys.exit('Quitting program')

# Main entry point.
if __name__ == '__main__':
    print('Here we go....')
    # Sets exit signals to call cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
  
    # Create the server
    tcp_server = None
    tcp_retry = 0
    while (tcp_server is None) or (tcp_retry == 10):
        try:
            tcp_server = ThreadedTCPServer(('localhost', 9999), ThreadedTCPRequestHandler)  
        except Exception as ex:
            tcp_retry += 1
            print('Attempt %d. Error in creating TCP Server: %s' % (tcp_retry, ex))
            if tcp_retry == 5:
                sys.exit('Cannot create TCP Server: %s' % ex)
            sleep(2)

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=tcp_server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    
    try:
        player = Player()   # Video player instance
    except Exception as ex:
        sys.exit('Unexpected error starting player: %s' % ex)
    
    # Run player main loop.
    player.run()

    while True:
        sleep(5)
