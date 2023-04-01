import subprocess as sub

class MagicNumber:

    # Begin serving
    BEGIN = 250

    # Begin getting destination filename
    TAKE_FILENAME = 251

    # Stop getting filename, start getting file content
    END_FILENAME = 252

    # Do nothing
    NOTHING = 253

    # Finish transcription
    FINISH = 254

    def is_magic_number(num: int):
        return num > 127

# Generates ICMP tcpdump lines
def dump():
    args = ('sudo', 'tcpdump', '-vl', 'icmp', 'and', 'inbound')
    with sub.Popen(args, stdout=sub.PIPE) as tcpdump:
        for line in tcpdump.stdout:
            yield line.decode()

# Parses the TTL (time to live) value from a tcpdump line
def parse_ttl(tcpdump_line: str):
    lines = tcpdump_line.split(', ')
    for line in lines:
        if line.startswith('ttl'):
            yield int(line.split()[1])

# Writes a char array to a file
def write_chars(chars: list, file: str):
    with open(file, 'ab') as f:
        f.write(''.join(chars).encode())


def main():

    take_filename = True
    file_name = ""
    chars = []
    begun = False

    for line in dump():
        for ttl in parse_ttl(line):

            # We don't begin until we receive the BEGIN magic number
            if not begun:
                if ttl == MagicNumber.BEGIN:
                    begun = True
                else:
                    continue

            if MagicNumber.is_magic_number(ttl):
                if ttl == MagicNumber.NOTHING:
                    continue

                elif ttl == MagicNumber.TAKE_FILENAME:
                    take_filename = True

                if ttl == MagicNumber.END_FILENAME:
                    take_filename = False

                elif ttl == MagicNumber.FINISH:
                    write_chars(chars, file_name)
                    begun = False

                continue

            byte_char = chr(ttl)
            if take_filename:
                file_name += byte_char
                continue

            if len(chars) < 1024:
                chars.append(byte_char)
                continue
            else: 
                write_chars(chars, file_name)
                chars = []


main()