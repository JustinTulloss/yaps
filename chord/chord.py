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

packet = Struct('!ih')

KSIZE = 32 #Keys are 32 bits for simplicity (that's what python already does)

class ChordBase(object):
    def __init__(self):
        # Build finger table
        self.finger = []
    def find_successor(self, key):
        current = self
        while self.distance(current.id, key) > \
                self.distance(current.next.id, key):
            current = current.next
        return current
            
        """
        next = self.find_predecessor(id)
        return next.successor
        """

    def find_predecessor(self, id):
        next = self.id
        while next < id <= next.successor:
            next = next.closest_preceding_finger(id)
        return next

    def closest_preceding_finger(self, id):
        for i in range(32, 1):
            if self.id <= finger[i].node.id <= id:
                return finger[i].node
        return self

    def distance(self, id, key):
        """
        Returns the distance of the key from the node identified by id
        """
        if id == key:
            return 0
        elif id < key:
            return key-id
        else:
            return (2**KSIZE)+(key-id)
        
class Chord(object):
    def __init__(self, localstore = True, **kwargs):
        """
        Inserts self into ring and initializes finger tables
        """

        if localstore:
            self._ls = ChordServer()

        logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger(__name__+'Chord')

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # key - size - value (network endianness)

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pvalue = pickle.dumps(value)
        msg = packet.pack(hash(key), len(pvalue))
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
        # Initialize socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, 4090))
        self._sock.listen(4)

        # Configure the logger
        logging.basicConfig(
            level = logging.DEBUG,
            format = '%(asctime)s %(levelname)s %(message)s',
            filename = './chordserver.log',
            filemode = 'w'
        )
        self._log = logging.getLogger(__name__+'.ChordServer')

        # Initialize thread to serve connections on said socket
        self._running = True
        self._accept_thread = threading.Thread(None, self.accept_loop)
        self._accept_thread.setDaemon(True)
        self._accept_thread.start()

    def __del__(self):
        self._running = False
        self._log.info("Closing Socket")
        self._sock.close()

    def accept_loop(self):
        self._log.info("Starting accept loop")
        try:
            while self._running:
                csock, addr = self._sock.accept()
                key = struct.unpack('!i', csock.recv(struct.calcsize('i')))[0]
                sizedata = csock.recv(struct.calcsize('h'))
                size = int(struct.unpack('!h', sizedata)[0])
                pobj = struct.unpack('!'+str(size)+'s', csock.recv(size))[0]
                obj = pickle.loads(pobj)
                self._log.debug("Received packet: %d, %d, %s", key, size, obj)
        except Exception, e:
            self._log.exception("Exception: %s", e)
            raise
        finally:
            self._log.info("Closing Socket")
            self._sock.close()

if __name__ == '__main__':
    c = Chord()
    c['trial'] = 45
    import time
    time.sleep(1) # Let the daemon thread finish doing stuff
