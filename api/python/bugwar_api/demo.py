
from bugwar_api import *
from time import sleep

start('bugwar')
success("bugwar success")
failure("bugwar fail")
error("bugwar error")
ASSERT(True, 'bugwar assert true')
assert_eq(2 + 2, 5, 'bugwar assert 2 + 2 == 5')
sleep(1)
stop()

