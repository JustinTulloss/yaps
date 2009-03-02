import stackless, sys
import cPickle
import pdb
import _dstack
import time
from Queue import Queue, Empty
import threading

# Message Types
TASK_NEW = 15
TASK_OP = 16
CH_SUBSCRIBE = 17
CH_UNSUBSCRIBE = 18
CH_PUBLISH = 19
CH_NEW = 20
CH_RECEIVED = 21
CH_DELIVERED = 22

class DStackException(Exception):
    pass

class _OurTasklet(stackless.tasklet):
    """
    This is just a normal tasklet, but it's only allowed to access channels
    that it has specifically asked for an exist in its channel dict. We need
    a subclass of stackless.tasklet so we can cPickle the channels dict. Oh, and
    its key.
    """
    key = None

    def __init__(self, *args):
        self.key = _dstack.make_key(self)
        super(_OurTasklet, self).__init__(*args)

    def __reduce_ex__(self, cPickleVersion):
        return self.__reduce__()

    def __reduce__(self):
        ret = list(super(_OurTasklet, self).__reduce__())
        l = list(ret[2])
        l.append(self.__dict__)
        ret[2] = tuple(l)
        return tuple(ret)
    
    def __setstate__(self, l):
        self.__dict__.update(l[-1])
        return super(_OurTasklet, self).__setstate__(l[:-1])

class Tasklet(object):
    """
    This class creates a tasklet and distributes it after it gets set up. It
    then acts like a proxy for the remote tasklet.
    """
    tasklet = None
    key = None

    def remote(func):
        name = func.__name__
        def newfunc(self, *args, **kwargs):
            if isinstance(self.tasklet, _OurTasklet):
                return func(self, *args, **kwargs)
            else:
                return self._distribute_msg(
                    name, 
                    *args, 
                    **kwargs
                )
        return newfunc

    def __init__(self, *args):
        if not node.started:
            node.start(4093)

        self.tasklet = _OurTasklet(*args)
        self.key = self.tasklet.key

    def _distribute(self):
        if self.tasklet:
            cPickled = cPickle.dumps(self.tasklet)
            _dstack.send(
                self.key,
                TASK_NEW, 
                cPickled
            )
            self.tasklet = None
        else:
            raise DStackException("You tried to distribute a proxy")

    def _distribute_msg(self, msg, *args, **kwargs):
        pargs = cPickle.dumps(args)
        pkwargs = cPickle.dumps(kwargs)
        msg = ';'.join((msg, pargs, pkwargs))

        if node.is_local(self.key):
            node.deliver(self.key, TASK_OP, msg)
        else:
            _dstack.send(
                self.key,
                TASK_OP,
                msg
            )

    @remote
    def __call__(self, *args, **kwargs):
        return self.setup(*args, **kwargs)

    @remote
    def setup(self, *args, **kwargs):
        self.tasklet.setup(*args, **kwargs)
        self.tasklet.remove()
        self._distribute()
        return self

    @remote
    def kill(self):
        pass

    @remote
    def bind(self, *args):
        pass

class Channel(stackless.channel):
    """
    This is meant to look like a regular channel, but it's not. It creates a
    real channel, puts it somewhere on the network, and then acts as a proxy to
    said channel
    """
    key = None
    name = None
    sendlock = stackless.channel()
    recvlock = stackless.channel()

    def __new__(type, *args, **kwargs):
        return super(stackless.channel, Channel).__new__(type)

    def __init__(self, name, distribute = False):
        self.key = _dstack.make_key(name, False)
        self.name = name
        super(Channel, self).__init__()
        if distribute:
            self._distribute()

    def __reduce_ex__(self, pickleVersion):
        return self.__reduce__()

    def __reduce__(self):
        ret = list(super(Channel, self).__reduce__())
        l = list(ret[1])
        l.append(self.name)
        ret[1] = tuple(l)
        l = list(ret[2])
        l.append(self.__dict__)
        ret[2] = tuple(l)
        return tuple(ret)
    
    def __setstate__(self, l):
        self.__dict__.update(l[-1])
        return super(Channel, self).__setstate__(l[:-1])

    def _distribute(self):
        pself = cPickle.dumps(self)
        _dstack.send(
            self.key,
            CH_NEW,
            pself
        )

    def receive(self):
        """
        If this channel isn't managed by this node, sign this node up to receive
        notifications about when messages are sent across it. 
        """
        node.add_receiver(self)
        return self.recvlock.receive()
    
    def send(self, value):
        node.add_sender(self, value)
        self.sendlock.receive() #wait for a response

    def delivered(self):
        """
        This is called when the channel is done sending. It means some tasklet
        has received the sent data
        """
        self.sendlock.send(None)

    def received(self, value):
        self.recvlock.send(value)

initialized = False
class StacklessNode(object):
    """
    This guy does all the dirty distributed stuff. It's singleton right now, so
    you can only belong to one distributed processing network at a time. Sorry.
    The derived channel and tasklet class rely heavily on the availability and
    interface of this class. It's not the prettiest thing in the world, but it
    kind of works.
    """
    initialized = False
    started = False
    tasklets = {}

    #dict of (channel, [blocking receivers], [blocking senders])
    local_channels = {}
    proxy_channels = {}

    _msgchannel = stackless.channel()

    def __init__(self):
        global initialized
        if not initialized:
            initialized = True
        else:
            raise DStackException(
                "Don't reinitialize me!(Use the start method)")

        # Set callbacks
        _dstack.set_update(self._handle_update)
        _dstack.set_deliver(self.deliver)

        # Set handlers
        self.message_handlers = {
            TASK_NEW: self.task_new,
            TASK_OP: self.task_op,
            CH_NEW: self.ch_new,
            CH_SUBSCRIBE: self.ch_subscribe,
            CH_UNSUBSCRIBE: self.ch_unsubscribe,
            CH_PUBLISH: self.ch_publish,
            CH_RECEIVED: self.ch_received,
            CH_DELIVERED: self.ch_delivered,
        }

        # Start stackless thread
        self._stackthread = threading.Thread(None, self._stackless_thread)
        #self._stackthread.setDaemon(True)
        self._stackthread.start()

    def _stackless_thread(self):
        """
        Starts the stackless loop in its own bg thread, so other things can
        happen
        """
        self._msgtasklet = stackless.tasklet(self.message_processor)()
        while True:
            stackless.run()

    def getkey(self):
        return _dstack.get_node_key()

    key = property(getkey, None, None, "The key of the stackless node")
        
    #### Channel stuff ####
    def add_receiver(self, ch):
        _dstack.send(
            ch.key,
            CH_SUBSCRIBE,
            self.key
        )

    def add_sender(self, ch, value):
        pvalue = cPickle.dumps(value)
        # We join the originating node id to the message so that if it
        # bounces back (ie, we have tasklets subscribed to this channel) we
        # don't deliver the message multiple times. A node can assume that
        # any message that originated at itself has been delivered to all
        # its local subscribers.
        msg = ';'.join((self.key, pvalue))
        _dstack.send(
            ch.key,
            CH_PUBLISH,
            msg
        )

    def make_channel(self, name):
        ch = Channel(name, distribute = True)

    def get_channel(self, name):
        key = _dstack.make_key(name, False)
        if self.is_local(key):
            self.proxy_channels[key] = self.local_channels[key][0]
            return self.local_channels[key][0]
        else:
            if self.proxy_channels.has_key(key):
                return self.proxy_channels[key]
            else:
                ch = Channel(name)
                self.proxy_channels[key] = ch
                return ch

    #### Message Processing Tasklet ####
    def message_processor(self):
        """
        This tasklet processes all messages coming in from other nodes on the
        system. It processes every message in the queue and then yields.
        """
        while True:
            key, type, message = self._msgchannel.receive()
            if (self.message_handlers.has_key(type)):
                stackless.tasklet(self.message_handlers[type])(key, message)
            stackless.schedule()

    def is_local(self, key):
        return self.tasklets.has_key(key) or self.local_channels.has_key(key)

    def start(self, port, bootstrap = None, extramodules=[]):
        if bootstrap:
            _dstack.init_network(port, ':'+bootstrap)
        else:
            _dstack.init_network(port)

        for module in extramodules:
            __import__(module, fromlist=['*'])

        self.started = True

    def deliver(self, *args):
        self._msgchannel.send(args)

    def _handle_update(self, key, message):
        # Check to see if the new node is responsible for any of the
        # tasklets currently running on this node
        pass


    ##### Handlers #####
    def task_new(self, key, message):
        if self.tasklets.has_key(key):
            print "Tasklet key collision on key", key
            return None

        # This tasklet came from far far away
        newt = cPickle.loads(message)

        """
        Put this in the list of tasklets we're managing. If it's alive, start
        to run it. Otherwise assume a message will come soon enough to liven it
        up.
        """
        self.tasklets[key] = newt
        if newt.alive:
            newt.insert()

    def task_op(self, key, message):
        fxn, args, kwargs = message.split(';', 2)
        args = cPickle.loads(args)
        kwargs = cPickle.loads(kwargs)
        getattr(self.tasklets[key], fxn)(*args, **kwargs)

    def ch_new(self, key, pchannel):
        channel = cPickle.loads(pchannel)
        self.local_channels[key] = (channel, [], [])
        
    def ch_subscribe(self, key, receiver):
        try:
            sender, message = self.local_channels[key][2].pop(0)
            _dstack.send(
                receiver,
                CH_RECEIVED,
                message
            )
            _dstack.send(
                sender,
                CH_DELIVERED,
                key
            )
        except IndexError:
            self.local_channels[key][1].append(receiver)

    def ch_unsubscribe(self, key, message):
        pass

    def ch_publish(self, key, message):
        channel, receivers, senders= self.local_channels[key]
        sender, pvalue = message.split(';', 1)
        newmessage = ';'.join((key, pvalue))

        try:
            # This is the linkage part. We send the message to a receiver and
            # send the confirmation of delivery to the sender
            receiver = receivers.pop(0)
            to_receiver = (
                receiver,
                CH_RECEIVED,
                newmessage
            )
            """
            if receiver == self.key:
                self._msgchannel.send(to_receiver)
            else:
                """
            _dstack.send(*to_receiver)

            to_sender = (
                sender,
                CH_DELIVERED,
                key
            )
            #if sender == self.key:
                #self._msgchannel.send(to_sender)
            #else:
            _dstack.send(*to_sender)

        except IndexError:
            #No receivers, block on send
            senders.append((sender, newmessage))

    def ch_received(self, key, message):
        ch_key, pvalue = message.split(';', 1)
        value = cPickle.loads(pvalue)
        # unblock a receiver
        ch = self.proxy_channels[ch_key]
        nada = ch.received(value)
    
    def ch_delivered(self, key, ch_key):
        # unblock a sender
        ch = self.proxy_channels[ch_key]
        ch.delivered()

node = StacklessNode()

def Ping():
    ping_channel = node.get_channel('ping_channel')
    pong_channel = node.get_channel('pong_channel')
    while True:
        print ping_channel.receive()
        print "PING"
        pong_channel.send("from ping")

def Pong():
    ping_channel = node.get_channel('ping_channel')
    pong_channel = node.get_channel('pong_channel')
    ping_channel.send('start')
    while True:
        print pong_channel.receive()
        print "PONG"
        ping_channel.send("from pong")

def MyTasklet(i):
    print "Hello!", i

def main():
    import time
    start = time.time()
    #node.start(4756, 'nascent:6789')
    node.start(4587)

    #for i in xrange(0, 5):
    #    t = Tasklet(MyTasklet)(i)

    """
    node.make_channel('ping_channel')
    node.make_channel('pong_channel')
    Tasklet(Ping)()
    Tasklet(Pong)()
    """
    for i in xrange(1, 500):
        (MyTasklet)(i)

    print "All tasklets created in %f" % (time.time() - start)

if __name__ == '__main__':
    main()
