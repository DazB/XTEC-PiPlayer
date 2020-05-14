import socket
import socketserver
import sys
from time import sleep
import threading

class PlayerTCPServer():
    """TCP Server that handles connections to control the passed in player"""

    def __init__(self, player):
        """Initalise TCP server and handler"""
        self.player = player

        # Dictionary of commands. Each one calls a different function in player
        self.command_dict = {
            b'LD': self.player.load_command,
            b'PL': self.player.play_command,
            b'LP': self.player.loop_command,
            b'PA': self.player.pause_command,
            b'ST': self.player.stop_command,
            b'SE': self.player.seek_command,
            b'VM': self.player.video_mute_command
        }

        # Try to create the server
        self.server = None
        tcp_retry = 0
        while self.server is None:
            try:
                self.server = self.ThreadedTCPServer(('localhost', 9999), self.dynamic_handler(self.command_dict))  
            except Exception as ex:
                if tcp_retry == 5:
                    sys.exit('TCP Server: Cannot create TCP Server: %s' % ex)
                
                tcp_retry += 1
                print('TCP Server: Attempt %d. Error in creating TCP Server: %s' % (tcp_retry, ex))
                sleep(2)

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

    def dynamic_handler(self, command_dict):
        """Function to dynamically create the TCP handler class, so we can 
        pass it the player functions for the handle method.
        Had to do this way, because don't know other way to pass just a class 
        that has been extended (in this case this TCP Handler class) to the Server class"""

        class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
            """TCP Request Handler class"""

            def __init__(self, *args):
                """Initalise with commands and pass rest to super"""
                self.command_dict = command_dict
                super().__init__(*args)

            def handle(self):
                """Handles incoming TCP data"""
                self.data = self.rfile.readline().strip()   # Get data
                
                print("{} wrote:".format(self.client_address[0]))
                print(self.data)

                # Get first 2 letters, then search dictionary to call corresponding command
                # Calls bad_command by default (essentially a switch, but python don't do switch)
                command = self.data[0:2]    
                command_func = self.command_dict.get(command, self.bad_command)
                try:
                    # Pass rest of the data packet to the function (could be nothing), and execute player command
                    msg_data = self.data[2:].decode()
                    response = command_func(msg_data)
                    # Respond with whatever player command returned
                    self.wfile.write(response.encode())

                except Exception as ex:
                    print("TCP Handle: Error processing command: " + str(ex))
                    self.bad_command()

            def bad_command(self):
                self.wfile.write('Error: unknown command'.encode())
                
        return ThreadedTCPRequestHandler    # return the class when function is called


    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        """TCP Server Class"""

        # Allow address to be reused (i.e. reopen after unexpected close)
        allow_reuse_address = True  

        def quit(self):
            """Shutdown TCP server"""
            self.shutdown()
            self.server_close()
            print('TCP Server: Shutdown')
