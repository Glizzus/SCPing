import subprocess as sub
import sys
from time import sleep
import os


def encode_num(num: int):
    """
    Encodes a number to give information about how to ping it.
    The number returned in the tuple is the ttl. The bool
    returned is whether to set the DF flag.
    """
    if 0 <= num <= 62:
        return (num + 64 + 1, False)
    elif 63 <= num <= 189:
        return (num + 64 + 1 + 1, False)
    elif 190 <= num <= 259:
        return (num - 128 + 1 + 1 + 1, True)
    return None


for i in range(500):
    print(i, encode_num(i))

exit()



def encode_char(char: str):
    """
    Encodes a charactor to give information about how to ping it.
    The number returned in the tuple is the ttl. The bool
    returned is whether to set the DF flag.
    """
    return encode_num(ord(char))


def encode_byte(byte: bytes) -> tuple[int, bool]:
    """
    Encodes a byte to give information about how to ping it.
    The number returned in the tuple is the ttl. The bool
    returned is whether to set the DF flag.
    """
    result = int.from_bytes(byte)
    return encode_num(result)


class MagicNumber:
    """Numbers that have special meaning to the server"""

    # Signals that the server should begin to interpret pings
    BEGIN = 256

    # Signals that the server should begin to take the destination filename
    TAKE_FILENAME = 257

    # Signals that the server should finish taking the destination filename
    END_FILENAME = 258

    # Signals that the transmission is over
    FINISH = 259


def ping_factory(host: str):
    """
    Returns a function that is used to ping the host.
    """

    def ping_windows(ttl: int, df: bool = False):
        args = ('ping', '-i', str(ttl), '-n', '1')
        if df:
            args += ('-f',)
        args += (host,)
        sub.Popen(args, stdout=sub.PIPE)

    def ping_linux(ttl: int, df: bool = False):
        args = ('ping', '-t', str(ttl))
        if df:
            args += ('-M', 'dont')
        args += (host,)
        sub.Popen(args, stdout=sub.PIPE)

    if os.name == 'nt':
        return ping_windows
    return ping_linux


def main():

    src_file = sys.argv[1]
    host, dest_file = sys.argv[2].split(':')

    ping = ping_factory(host)

    ping(64)
    sleep(1)

    ping(*encode_num(MagicNumber.BEGIN))
    ping(*encode_num(MagicNumber.TAKE_FILENAME))

    for char in dest_file:
        ping(*encode_char(char))

    ping(*encode_num(MagicNumber.END_FILENAME))

    with open(src_file, 'rb') as f:
        byte = f.read(1)
        while byte:
            ping(*encode_byte(byte))
            byte = f.read(1)

    ping(*encode_num(MagicNumber.FINISH))


main()
