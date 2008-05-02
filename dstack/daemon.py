import dstack
import sys, os
import time
from getopt import getopt, GetoptError
from dstack import *
from dstack import _OurTasklet

USAGE = """
Usage:
    -h, --help          print this
    -m, --module        module to serve
    -p, --port          port to serve on
    -b, --bootstrap     existing server to connect to
"""

def main(argv):
    try:
        opts, args = getopt(argv, "s:p:b", ["script=", "port=", "bootstrap="])
    except GetoptError:
        print USAGE
        sys.exit(2)

    # Defaults
    script = None
    port = 6789
    bootstrap = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        if opt in ("-s", "--script"):
            script = arg
        if opt in ("-p", "--port"):
            port = arg
        if opt in ("-b", "--bootstrap"):
            bootstrap = arg

    sys.path.insert(0,os.path.dirname(script))
    module = os.path.splitext(os.path.split(script)[1])[0]
    dstack.node.start(port, bootstrap, extramodules=[module])

    print "started netmgr on", port

    while True:
        time.sleep(400)

if __name__ == '__main__':
    main(sys.argv[1:])
