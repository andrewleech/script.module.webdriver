__author__ = 'corona'
from _utils import *
from js_fn import keycodeToKeyname, keynameToKeycode
import threading

import xbmcclient

# from socket import *

class KeySender(object):

    def __init__(self):
        self._client_lock = threading.Lock()
        self._closed = threading.Event()

        self.client = xbmcclient.XBMCClient(name="Browser")
        self.client.connect()

        self._pingThread = threading.Thread(target=self.ping_thread)
        self._pingThread.daemon = True
        self._pingThread.start()

    def close(self):
        self._closed.set()
        with self._client_lock:
            self.client.close()

    def ping_thread(self):
        while not self._closed.is_set():
            # required ping every 60 seconds to keep connection alive
            for _ in range(40):
                sleep(1)

            with self._client_lock:
                self.client.ping()

    def send_key(self, keystrokes):

        # IMPORTANT: After a HELO packet is sent, the client needs to "ping" XBMC
        # at least once every 60 seconds or else the client will time out.
        # Every valid packet sent to XBMC acts as a ping, however if no valid
        # packets NEED to be sent (eg. the user hasn't pressed a key in 50 seconds)
        # then you can use the PacketPING class to send a ping packet (which is
        # basically just an empty packet). See below.

        # Once a client times out, it will need to reissue the HELO packet.
        # Currently, since this is a unidirectional protocol, there is no way
        # for the client to know if it has timed out.

        for key in list(keystrokes):

            # press key
            code = key.get('keyCode')
            keyName = keycodeToKeyname.get(code)
            if keyName:
                with self._client_lock:
                    self.client.send_keyboard_button(keyName)
                    sleep(0.2)
                    self.client.release_button()

    def __del__(self):
        self.close()