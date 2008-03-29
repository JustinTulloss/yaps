"""
Implements a chord-like distributed hash table in python. This is purely
for storing python objects.

Justin Tulloss
"""
import logging
import socket
import struct
from struct import Struct
import cPickle
import threading
import hashlib


KSIZE = 32 #Keys are 32 bits for simplicity (that's what python already does)

"""
class Chord(object):
    def __init__(self, localstore = True, **kwargs):
        Inserts self into ring and initializes finger tables

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
"""

class Node(object):
    def __init__(self, ip, port):
        self.id = hash((ip, port))
        self.ip = ip
        self.port = port
        self._successor = None
        self._predecessor = None
        self.finger = range(0, KSIZE-1)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start =  int((self.id + 1) % 2**KSIZE)

    def find_successor(self, id):
        """
        query this node for a successor
        """
        return self.find_predecessor(id).successor

    def find_predecessor(self, id):
        """
        query this node for its predecessor
        """
        pass

    def join(self, seedNode):
        if seedNode == None:
            for i in range(0, KSIZE-1):
                self.finger[i] = self
            predecessor = self
        else:
            self.init_finger_tables(seedNode)

    def init_finger_tables(self, seedNode):
        self.finger[0] = self.node
        self.successor = seedNode.find_successor(self.finger[1].start)
        self.predecessor = self.node.successor.predecessor
        self.successor.predecessor = self.node
        for i in range(0, KSIZE-2):
            next_start = int((self.node.id+2**i)%2**KSIZE)
            if self.node.id <= next_start < self.finger[i].id:
                self.finger[i+1].successor = finger[i].successor
            else:
                self.finger[i+1].successor = seedNode.find_successor(next_start)

    def update_others(self):
        for i in range(1, KSIZE):
            p = self.find_predecessor(self.id-2**(i-1))
            p.update_finger_table(self, i)


    def update_finger_table(self, node, i):
        if self.id <= node.id < finger[i].id:
            self.finger[i] = node
            # TODO: Call the node and inform it of the change
            self.predecessor.update_finger_table(node, i)

    def get_successor(self):
        if self._successor == None:
            self._successor = self.find_successor(self, self.id)
        return self._successor

    successor = property(get_successor, None, None, 
        "The node adjacent to this node in the ring")

    def get_predecessor(self):
        if self._predecessor== None:
            self._predecessor = self.find_predecessor(self, self.id)
        return self._predecessor

    def set_predecessor(self, node):
        self._predecessor = node
        # Actually call the node and tell it that its predecessor has changed

    predecessor = property(get_predecessor, set_predecessor, None, 
        "The node behind this node in the ring")


class Chord(object):
    def __init__(self, seedNode=None, ip='127.0.0.1', port=4090):
        self.packet = Struct('!bih')
        # Configure the logger
        logging.basicConfig(
            level = logging.DEBUG,
            format = '%(asctime)s %(levelname)s %(message)s',
            filename = './chordserver.log',
            filemode = 'w'
        )
        self._log = logging.getLogger(__name__+'.ChordServer')

        # Create yourself!
        self.node = Node(ip = ip, port = port)
        self.node.join(seedNode)
        # Initialize socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(('0.0.0.0', port))
        self._sock.listen(4)

        # Initialize thread to serve connections on said socket
        self._running = True
        self._accept_thread = threading.Thread(None, self.accept_loop)
        self._accept_thread.setDaemon(True)
        self._accept_thread.start()

    def __del__(self):
        self._running = False
        self._log.info("Closing Socket")
        if self._sock != None:
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
    import netifaces
    ip = netifaces.ifaddresses('eth1')[netifaces.AF_INET][0]['addr']
    c = Chord(ip = ip)
    d = Chord(ip = ip, port=4091)
    #c['trial'] = 45
    import time
    time.sleep(1) # Let the daemon thread finish doing stuff
