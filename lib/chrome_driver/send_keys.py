__author__ = 'corona'

lib_path = os.path.join(os.path.dirname(__file__),'..')
if lib_path not in sys.path:
    sys.path.append(lib_path)

import time
import xbmcclient

from socket import *

class KeySender(object):
    def __init__(self):
        # connect to localhost, port 9777 using a UDP socket
        # this only needs to be done once.
        # by default this is where XBMC will be listening for incoming
        # connections.
        host = "localhost"
        port = 9777
        self.addr = (host, port)
        self.sock = socket(AF_INET,SOCK_DGRAM)
        # First packet must be HELO
        self._HELO()

    def _HELO(self):
        xbmcclient.PacketHELO(devicename="ChromeDriver").send(self.sock, self.addr)

    def send_key(self, keystroke):

        # IMPORTANT: After a HELO packet is sent, the client needs to "ping" XBMC
        # at least once every 60 seconds or else the client will time out.
        # Every valid packet sent to XBMC acts as a ping, however if no valid
        # packets NEED to be sent (eg. the user hasn't pressed a key in 50 seconds)
        # then you can use the PacketPING class to send a ping packet (which is
        # basically just an emppty packet). See below.

        # Once a client times out, it will need to reissue the HELO packet.
        # Currently, since this is a unidirectional protocol, there is no way
        # for the client to know if it has timed out.

        self._HELO()
        for char in list(keystroke):

            # press key
            packet = xbmcclient.PacketBUTTON(code=char, queue=1)
            packet.send(self.sock, self.addr)

    def __del__(self):
        packet = xbmcclient.PacketBYE()    # PacketPING if you want to ping
        packet.send(self.sock, self.addr)
        self.sock.close()
