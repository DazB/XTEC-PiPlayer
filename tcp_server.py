import socket
import socketserver
import sys
from time import sleep
import threading

class PlayerTCPServer():

    def __init__(self, player):
        self.player = player
        # Dictionary of commands
        self.command_dict = {
            b'PL': self.player.play
        }

        # Create the server
        self.server = None
        tcp_retry = 0
        while self.server is None:
            try:
                self.server = self.ThreadedTCPServer(('localhost', 9999), self.shit(self.command_dict))  
            except Exception as ex:
                tcp_retry += 1
                print('Attempt %d. Error in creating TCP Server: %s' % (tcp_retry, ex))
                if tcp_retry == 5:
                    sys.exit('Cannot create TCP Server: %s' % ex)
                sleep(2)

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

    def shit(self, command_dict):
        class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
            """TCP Request Handler class"""

            def __init__(self, *args):
                self.command_dict = command_dict
                super().__init__(*args)

            def handle(self):
                self.data = self.rfile.readline().strip()   # Get data
                
                print("{} wrote:".format(self.client_address[0]))
                print(self.data)

                command = self.data[0:2] 
                command_func = self.command_dict.get(command, self.unknown_command)
                command_func()

            def unknown_command(self):
                print('Unknown command')
                
        return ThreadedTCPRequestHandler


    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        """TCP Server Class"""

        # Allow address to be reused (i.e. reopen after unexpected close)
        allow_reuse_address = True  

        def quit(self):
            """Cleanup TCP server"""
            self.shutdown()
            self.server_close()
            print('TCP Shutdown')
