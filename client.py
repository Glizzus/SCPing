import subprocess as sub
import sys
from time import sleep


def encode_num(num: int):
    """
    Encodes a number to give information about how to ping it.
    The number returned in the tuple is the ttl. The bool
    returned is whether to set the DF flag.
    """
    if 0 <= num <= 62:
        return (num + 65, False)
    elif 63 <= num <= 189:
        return (num + 65 + 1, False)
    elif 190 <= num <= 259:
        # I don't know why we add 3 here. It works though
        return (num - 128 + 3, True)


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

    def ping(ttl: int, df: bool = False):
        """
        Performs the ping command.
        """
        args = ('ping', '-i', str(ttl), '-n', '1')
        if df:
            args += ('-f',)
        args += (host,)
        sub.Popen(args, stdout=sub.PIPE)
    return ping


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
