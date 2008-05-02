import time
import dstack
from dstack import _OurTasklet
from dstack import *

dstack.node.start(1232, 'nascent:6789')

print "started netmgr on 1232"

while True:
    time.sleep(400)
