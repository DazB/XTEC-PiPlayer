import os
import threading

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

class XtecFTPServer:
    """The FTP Server for the player"""

    def __init__(self, username, password, ip, port):
        """Initalise FTP"""
        # Instantiate a dummy authorizer for managing 'virtual' users
        authorizer = DummyAuthorizer()

        # Define a new user having full r/w permissions and a read-only
        # anonymous user
        authorizer.add_user(username, password, '/home/pi/XTEC-PiPlayer/testfiles/', perm='elradfmwMT')
        authorizer.add_anonymous(os.getcwd())

        # Instantiate FTP handler class
        self.handler = FTPHandler
        self.handler.authorizer = authorizer

        # Define a customized banner (string returned when client connects)
        self.handler.banner = "MP2 FTP Interface"

        # Instantiate FTP server class
        address = (ip, int(port))
        self.server = FTPServer(address, self.handler)

        # set a limit for connections
        self.server.max_cons = 5
        self.server.max_cons_per_ip = 5

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        self.ftp_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        self.ftp_thread.daemon = True
        # start ftp server
        self.ftp_thread.start()