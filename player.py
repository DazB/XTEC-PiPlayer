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
        self.player.play()

    def quit(self):
        """Shut down program"""
        print('Player Shutdown')

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """TCP Request Handler class"""

    def handle(self):
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP Server Class"""
    # Allow address to be reused (i.e. reopen after unexpected close)
    allow_reuse_address = True  

    def quit(self):
        """Cleanup TCP server"""
        self.shutdown()
        self.server_close()
        print('TCP Shutdown')

class GracefulExit:

    def __enter__(self):
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)

    def __exit__(self, type, value, traceback):
        pass

    def quit(self, signum, stack):
        print('Received signal: ', signum)

def cleanup(signum, frame):
    """Cleanup function. Calls cleanup functions in each class"""
    # TODO: is there a better way to do this? Global function seems wrong
    print('Cleaning up')
    ThreadedTCPServer.quit
    Player.quit

# Main entry point.
if __name__ == '__main__':
    print('Here we go....')
    # Sets exit signals to call cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
  
    # Try create the server
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
