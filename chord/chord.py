"""
Implements a chord-like distributed hash table in python. This is purely
for storing python objects.

Justin Tulloss
"""
import logging
import socket
import struct
from struct import Struct
import Pyro.core
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

class Node(Pyro.core.ObjBase):
    def __init__(self, ip, port):
        Pyro.core.ObjBase.__init__(self)
        self.addr = (ip, port)
        self.id = hash(self.addr)
        self.url = 'http://%s:%d' % self.addr
        self.ip = ip
        self.port = port
        self._successor = None
        self._predecessor = None
        self.finger = range(0, KSIZE-1)
        self.start =  int((self.id + 1) % 2**KSIZE)

    def find_successor(self, id):
        """
        query this node for a successor
        """
        node = self.find_predecessor(id).successor
        return node

    def find_predecessor(self, id):
        """
        query this node for its predecessor
        """
        p = self;
        while p.id < id <= p.successor.id:
            p = p.closest_precceding_finger(id)
        return p

    def closest_preceding_finger(self, id):
        for i in range(KSIZE-1, 0, -1):
            if self.id < finger[i].id < id:
                return finger[i]
        return self.getAttrProxy()

    def join(self, seedNode):
        # I know this looks bad, but using the type avoids an RPC request
        if type(seedNode) != type(None):
            self.init_finger_tables(seedNode)
        else:
            for i in range(0, KSIZE-1):
                self.finger[i] = self.getAttrProxy()
            self._predecessor = self.getAttrProxy()
            self._successor = self.getAttrProxy()

    def init_finger_tables(self, seedNode):
        next_start = int((self.id+2)%2**(KSIZE-1))
        self.finger[0] = seedNode.find_successor(next_start)
        self.successor = self.finger[0]
        self.predecessor = self.successor.predecessor
        self.successor.predecessor = self.getAttrProxy()
        for i in range(0, KSIZE-1):
            if self.id <= next_start < self.finger[i].id:
                self.finger[i+1].successor = finger[i].successor
            else:
                next_start = int((self.id+2**i)%2**(KSIZE-1))
                self.finger[i+1].successor = seedNode.find_successor(next_start)
        print self.finger

    def update_others(self):
        for i in range(1, KSIZE-1):
            p = self.find_predecessor(self.id-2**(i-1))
            p.update_finger_table(self, i)


    def update_finger_table(self, node, i):
        if self.id <= node.id < finger[i].id:
            self.finger[i] = node
            self.predecessor.update_finger_table(node, i)

    def get_successor(self):
        #if self._successor == None:
        #    self._successor = self.find_successor(self.id)
        return self._successor

    def set_successor(self, node):
        self._successor = node

    successor = property(get_successor, set_successor, None, 
        "The node adjacent to this node in the ring")

    def get_predecessor(self):
        #if self._predecessor== None:
        #    self._predecessor = self.find_predecessor(self.id)
        return self._predecessor

    def set_predecessor(self, node):
        self._predecessor = node

    predecessor = property(get_predecessor, set_predecessor, None, 
        "The node behind this node in the ring")

    def get_id(self):
        return self.id


class Chord(object):
    def __init__(self, seedNode=None, ip='127.0.0.1', port=4090):
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

        # Initialize server
        Pyro.core.initServer()
        self._daemon = Pyro.core.Daemon(host=ip, port=port)
        self._uri = self._daemon.connect(self.node)

        self.node.join(seedNode)

        # Initialize thread to serve connections on said socket
        self._accept_thread = threading.Thread(None, self.accept_loop)
        #self._accept_thread.setDaemon(True)
        self._accept_thread.start()

    def __del__(self):
        self._log.info("Closing Socket")
        if self._sock != None:
            self._sock.close()
    
    def accept_loop(self):
        self._log.info("Starting accept loop")
        try:
            self._daemon.requestLoop()
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
    known = Pyro.core.getAttrProxyForURI(c._uri)
    d = Chord(seedNode = known, ip = ip, port=4091)
    #c['trial'] = 45
    import time
    time.sleep(1) # Let the daemon thread finish doing stuff
