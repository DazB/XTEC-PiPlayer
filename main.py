#!/usr/bin/env python3

#######################################
## Pi Player
#######################################

import sys
import signal
import time
import logging

from tcp_server import PlayerTCPServer
from player import Player

class App:
    """Main Application class"""

    def __init__(self):
        """Creates all the needed application objects"""
        # Try to create the player
        self.player = None
        player_retry = 0
        PLAYER_RETRY_DELAY = 2
        PLAYER_MAX_RETRIES = 5
        while self.player is None:
            try:
                self.player = Player()   # Video player instance
            except Exception as ex:
                if player_retry == PLAYER_MAX_RETRIES:
                    sys.exit('Cannot create Player. Is the path correct? : %s' % ex)
                player_retry += 1
                print('Attempt %d. Error in creating player: %s' % (player_retry, ex))
                time.sleep(PLAYER_RETRY_DELAY)

        # Create the server
        self.player_tcp_server = PlayerTCPServer(self.player)

    def run(self):
        """Main app loop"""
        while True:
            pass

    def cleanup(self):
        """Application cleanup"""
        print('App: Cleaning up')
        self.player_tcp_server.server.quit()
        self.player.quit()
        sys.exit('App: Quitting. Goodbye')     


# Main entry point.
if __name__ == '__main__':
    print('And here we go....')

    LOG_FILENAME = 'debug.log'
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)

    # Main app instance
    app = App()

    # Sets app exit signals to call cleanup
    signal.signal(signal.SIGINT, app.cleanup)
    signal.signal(signal.SIGTERM, app.cleanup)

    # Run the app :D
    app.run()
