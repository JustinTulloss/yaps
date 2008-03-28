"""
Implements a chord-like distributed hash table in python. This is purely
for storing python objects.

Justin Tulloss
"""
import logging
import socket
import struct
from struct import Struct
import pickle
import threading
import hashlib

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

packet = Struct('!40sh')

class Chord(object):
    def __init__(self, localstore = True, **kwargs):
        """
        Inserts self into ring and initializes finger tables
        """

        if localstore:
            self._ls = ChordServer()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # key - size - value (network endianness)

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        sha = hashlib.sha1(key)

        pvalue = pickle.dumps(value)
        msg = packet.pack(sha.hexdigest(), len(pvalue))
        msg = "%s%s" % (msg, pvalue)
        self._sock.connect(('localhost', 4090))
        self._sock.send(msg)

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

    def __del__(self):
        self._running = False

    def accept_loop(self):
        try:
            log.info("Starting accept loop")
            while self._running:
                csock, addr = self._sock.accept()
                key = struct.unpack('!40s', csock.recv(40))[0]
                sizedata = csock.recv(struct.calcsize('h'))
                size = int(struct.unpack('!h', sizedata)[0])
                pobj = struct.unpack('!'+str(size)+'s', csock.recv(size))[0]
                obj = pickle.loads(pobj)
        finally:
            log.info("Closing Socket")
            self._sock.close()

if __name__ == '__main__':
    c = Chord()
    c['trial'] = 45
