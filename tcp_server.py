import socket
import socketserver
import sys
from time import sleep
import threading

class PlayerTCPServer():
    """TCP Server that handles connections to control the passed in player"""

    def __init__(self, player, port):
        """Initalise TCP server and handler"""
        self.player = player

        # Dictionary of commands. Each one calls a different function in player
        self.command_dict = {
            'LD': self.player.load_command,
            'PL': self.player.play_command,
            'LP': self.player.loop_command,
            'PA': self.player.pause_command,
            'ST': self.player.stop_command,
            'SE': self.player.seek_command,
            'VM': self.player.video_mute_command,
            'AM': self.player.audio_mute_command
        }

        # Try to create the server
        self.server = None
        tcp_retry = 0
        while self.server is None:
            try:
                self.server = self.ThreadedTCPServer(('0.0.0.0', int(port)), self.dynamic_handler(self.command_dict))  
            except Exception as ex:
                if tcp_retry == 5:
                    print('TCP Server: Cannot create TCP Server: %s' % ex)
                    return
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
                while True:
                    self.data = self.rfile.readline() # Get data
                    
                    # Keeps connection open until client disconnects
                    if not self.data:
                        print("Client {} disconnected".format(self.client_address[0]))
                        break

                    print("{} wrote:".format(self.client_address[0]))
                    print(self.data)

                    # Send acknowledgment that we've received the data
                    self.wfile.write(('R\r').encode())
                    
                    # Strip whitespace
                    self.data = self.data.strip()
                    
                    # Get last 2 letters, then search dictionary to call corresponding command
                    # Calls bad_command by default (essentially a switch, but python don't do switch)
                    command = self.data[-2:].decode().upper()
                    command_func = self.command_dict.get(command, self.bad_command)
                    try:
                        # Pass rest of the data packet to the function (could be nothing), and execute player command
                        msg_data = self.data[:-2].decode().upper()
                        msg_data = msg_data.lstrip()
                        msg_data = msg_data.strip()
                        response = command_func(msg_data)
                        # Respond with data appended with what command returned
                        self.wfile.write(response.encode())

                    except Exception as ex:
                        print("TCP Handle: Error processing command: " + str(ex))
                        self.wfile.write(('ER\r').encode())

            def bad_command(self, *args):
                return 'ER\r'
                
        return ThreadedTCPRequestHandler    # return the class when function is called


    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        """TCP Server Class"""

        # Allow address to be reused (i.e. reopen after unexpected close)
        allow_reuse_address = True  

        def quit(self):
            """Shutdown TCP server"""
            print('TCP Server: Shutdown')
            self.shutdown()