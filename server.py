import subprocess as sub
from sys import byteorder
from shutil import which


def tcpdump_exists():
    return which('tcpdump') is not None


def represent_as_word(num: int):
    return num.to_bytes(2, byteorder)


def ping_value_to_word(ttl: int):
    """
    Takes an integer value and maps it back to its value
    as a word.

    128 is the default ttl for Windows, and 64 is the default
    ttl for Linux. Therefore, we want to skip these values.
    We also only want to listen to ttl values above 64 so that
    each byte has a chance of making it to its destination.

    Remember that the ttl is a byte, and we use the DF flag
    as the 9th bit.

    This means that, when we do values above 255 by setting the DF
    flag, we can't go straight to 256 because it would have a ttl of 0 since
    the ttl is the first 8 bits.

    This means that the soonest number we accept after 255 is 321.

    1 0 1 0 0 0 0 0 1
      ---------------
           ttl

    because this maintains the ttl above 64.
    """

    def to_int():
        if 64 < ttl < 128:
            return ttl - 65
        elif 128 < ttl < 256:
            return ttl - 65 - 1
        elif 320 < ttl < 391:
            return ttl - 65 - 1 - 65
        else:
            return -1

    result = to_int()
    if result < 0:
        return None
    return represent_as_word(result)


class MagicWord:
    """Words that have special meaning to our server"""

    # Signals that this server is to begin interpreting pings
    BEGIN = represent_as_word(256)

    # Signals that this server is ready to receive the destination filename
    TAKE_FILENAME = represent_as_word(257)

    # Signals that this server is done receiving the destination filename
    END_FILENAME = represent_as_word(258)

    # Signals that this server is done interpreting pigns
    FINISH = represent_as_word(259)


def dump():
    """Generates ICMP tcpdump lines"""
    args = ('sudo', 'tcpdump', '-vl', 'icmp', 'and', 'inbound')
    with sub.Popen(args, stdout=sub.PIPE) as tcpdump:
        for line in tcpdump.stdout:
            yield line.decode()


def parse_ttl(tcpdump_line: str):
    """
    Parses the word from the given tcpdump line.
    The ttl value represents the first 8 bits of the word,
    and whether the DF bit is set represents the 8th bit.
    """
    val = 0
    lines = tcpdump_line.split(', ')
    for line in lines:
        if (line.startswith('ttl')):
            val += int(line.split()[1])
        if (line.startswith('flags')):
            flag = line.split()[1]
            # The DF Flag represents the 9th bit
            if "DF" in flag:
                val += 256
    return -1 if not val else val


def listen():
    """Listens for ICMP traffic and generates words."""
    for line in dump():
        val = parse_ttl(line)
        if val:
            yield represent_as_word(val)


def write_byte_list(byt: list, file_name: str):
    """Writes a list of bytes to the given file"""
    data = b''.join(byt)
    with open(file_name, 'ab') as file:
        file.write(data)


def main():

    file_mode = True
    begun = False
    filename = ""
    data = []

    if not tcpdump_exists():
        print('Cannot find executable tcpdump. Make sure it is in your path')
        exit(1)

    def flush_buffer():
        nonlocal data, filename
        write_byte_list(data, filename)

    for word in listen():
        if word == MagicWord.BEGIN:
            begun = True
        elif word == MagicWord.TAKE_FILENAME:
            file_mode = True
        elif word == MagicWord.END_FILENAME:
            file_mode = False
        elif word == MagicWord.FINISH:
            flush_buffer()
            begun = False
            print('Finished writing', filename)
        elif not begun:
            return
        else:
            main_byte = word[0:1]
            if file_mode:
                char = main_byte.decode()
                filename += char
            else:
                # We use a buffer to save on writes to the file
                if len(data) < 4096:
                    data.append(main_byte)
                else:
                    print('writing a buffer')
                    flush_buffer()


main()
