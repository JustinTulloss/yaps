import sys
sys.path.append('../')
import chimera

USAGE = "test [ -j bootstrap:port ] port key"
TEST_CHAT = 15

def test_fwd(key, msg, host):
    print "Routing %s (%s) to %s via %:%d" % \
        msg.type, msg.payload, key.keystr, host.name, host.port

def test_del(key, msg):
    print "Delivered %s (%s) to %s" %\
        msg.type, msg.payload, key.keystr

def test_update(key, host, joined):
    if joined:
        verb = 'joined'
    else:
        verb = 'leaving'
    
    print "Node %s:%s:%d %s neighborhood set" %  \
            key.keystr, host.name, host.port, verb

def main():
    bhost = None
    sys.argv.pop(0)
    if '-j' in sys.argv:
        i = l.index('-j')
        l.remove('-j')
        bootstrap = l.pop(i+1)
        try:
            bhost, bport = bootstrap.split(':')
        except:
            print "Invalid option"
            print USAGE
            exit()

    if len(sys.argv) != 2:
        print USAGE
        exit()

    port = int(sys.argv[0])
    mykey = chimera.Key()
    chimera.str_to_key(sys.argv[1], mykey)

    state = chimera.chimera_init(port)
    if state == None:
        print "Unable to initialize chimera"
        exit()

    if bhost!= None:
        bhost = chimera.host_get(state, bhost, bport)

    """
    chimera.chimera_forward(state, test_fwd)
    chimera.chimera_deliver(state, test_del)
    chimera.chimera_update(state, test_update)
    """
    chimera.chimera_setkey(state, mykey)
    chimera.chimera_register(state, TEST_CHAT, 1)

    chimera.log_direct(state.log, chimera.LOG_WARN, sys.stderr)
    #chimera.log_direct(state.log, chimera.LOG_ROUTING, sys.stderr)

    chimera.chimera_join(state, bhost)

    print "** send messages to key with command <key> <message> **"

    key = chimera.Key()
    try:
        while 1:
            tmp = raw_input()
            if len(tmp) > 2:
                chimera.str_to_key(tmp, key)
                #print "Sending key:%s data:%s len:%d" %\
                #    key.keystr, tmp, len(tmp)
                chimera.chimera_send(state, key, TEST_CHAT, len(tmp), tmp)

    except EOFError, e:
        exit()

if __name__ == '__main__':
    main()
