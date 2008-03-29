"""
Implements a chord-like distributed hash table in python. This is purely
for storing python objects.

Justin Tulloss
"""
import logging
import socket
import struct
from struct import Struct
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Server
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

class Messages(object):
    ID, SUCCESSOR, PREDECESSOR = range(0,3)

cmsgs = Messages()

class Node(object):
    def __init__(self, ip, port):
        self.addr = (ip, port)
        self.id = hash(self.addr)
        self.ip = ip
        self.port = port
        self.finger = range(0, KSIZE-1)
        self.start =  int((self.id + 1) % 2**(KSIZE-1))

    def find_successor(self, node, id):
        """
        query this node for a successor
        """
        node = self.find_predecessor(node, id)
        return node

    def find_predecessor(self, id):
        """
        query this node for its predecessor
        """
        p = self.addr;
        while self.get_id(p) < id <= self.get_id(self.get_succesor(p))
            p = p.closest_precceding_finger(id)
        return p

    def closest_preceding_finger(self, id):
        for i in range(KSIZE-1, 0, -1):
            if self.id < self.get_id(finger[i]) < id:
                return finger[i]
        return self.addr

    def join(self, seedNode):
        # I know this looks bad, but using the type avoids an RPC request
        if type(seedNode) != type(None):
            self.init_finger_tables(seedNode)
        else:
            for i in range(0, KSIZE-1):
                self.finger[i] = self.addr

    def init_finger_tables(self, seedNode):
        self.finger[0] = self.find_successor(seedNode, self.start)
        self._predecessor = self.get_predecessor(self.finger[0])
        self.set_predecessor(self.finger[0], self.addr)
        for i in range(0, KSIZE-1):
            next_start = int((self.id+2**i)%2**(KSIZE-1))
            if self.id <= next_start < self.get_id(self.finger[i]):
                self.finger[i+1] = finger[i]
            else:
                self.finger[i+1] = self.find_successor(seedNode, next_start)

    def update_others(self):
        for i in range(1, KSIZE-1):
            p = self.find_predecessor(self.id-2**(i-1))
            p.update_finger_table(self, i)


    def update_finger_table(self, node, i):
        pass

    def get_successor(self):
        pass

    def set_successor(self, node):
        pass

    def get_id(self, node):
        
        
    def get_predecessor(self):
        pass

    def set_predecessor(self, node):
        pass

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
        self.node.join(seedNode)

        # Initialize server
        self._server = SimpleXMLRPCServer((ip, port))
        self._server.register_introspection_functions()
        self._server.register_instance(self.node)

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
            self._server.serve_forever()
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
    known = Server('http://'+ip+':4090', allow_none=True)
    d = Chord(seedNode = known, ip = ip, port=4091)
    #c['trial'] = 45
    import time
    time.sleep(1) # Let the daemon thread finish doing stuff
