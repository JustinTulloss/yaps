"""
Implements a chord-like distributed hash table in python

Justin Tulloss
"""
import logging
import socket
import threading
import hashlib

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

class Chord(object):
    def __init__(self, localstore = True, **kwargs):
        """
        Inserts self into ring and initializes finger tables
        """

        if localstore:
            self._ls = ChordServer()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __getitem__(self, key):
        log.debug(key)

    def __setitem__(self, key, value):
        sha = hashlib.sha1(key)

        self._sock.connect(('localhost', 4090))
        self._sock.send(sha.digest())

    def __delitem__(self, key):
        pass

    def __repr__(self):
        return "Hello World!"

    def __iter__(self):
        pass

    def __len__(self):
        pass

    def clear(self):
        pass

class ChordServer(object):
    def __init__(self, host='localhost'):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, 4090))
        self._sock.listen(4)
        self._running = True
        self._accept_thread = threading.Thread(None, self.accept_loop)
        self._accept_thread.setDaemon(True)
        self._accept_thread.start()

    def accept_loop(self):
        while self._running:
            csock, addr = self._sock.accept()
            log.debug("Client at %s", addr)

