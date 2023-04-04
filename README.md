# SCPing

Unidirectional file transfer using `ping` and `tcpdump`.

Currently, this only supports file upload. I have no clue if Bidirectional file transfer is possible as of now.

Also, because ICMP is not intended for streaming, sometimes bytes will be out of order. This may render images corrupted and binaries unusable. This may be best used for plain text exfiltration, where errors can easily be spotted and fixed.

## Prerequisites

The server requires `tcpdump`. Additionally, it must be in your system `PATH` variable.

`tcpdump` installation:

Debian / Ubuntu

`apt-get install tcpdump`

CentOS / RHEL

`dnf install tcpdump`

## To use

Server side: 

`python server.py`

(`sudo` privileges are required)

Client side: Run using SCP syntax

Example:

`python client.py catpicture.jpg 192.168.1.1:/home/users/jdoe/Pictures/cat.jpg`

## How it works

The information is sent over using two fields of the `ping` command: `ttl` (time to live) and `DF` (don't fragment).

`ttl` represents the amount of hops a ping can make before it gives up. If you set your `ttl` to be 64 and ping a host 65 hops away, then that ping will not reach the host.

`ttl` has to be in the range 1 to 255, so this gives us almost a byte of information. Remember though, that if our `ttl` is too low, then the ping may not reach the host.

Also, the default value for `ttl` is 128 on Windows and 64 on Linux. In order to avoid reading random pings that aren't from our client, we should also avoid reading pings with a ttl of 64 or 128.

We now have a problem; we need to transfer a file byte by byte, but we can't use the numbers 0, 64, or 128. Additionally, some `ttl` values may be too low and not reach the host.

We solve these problems by introducing the `DF` flag as a 9th bit, and not reading `ttl` values of 64 or lower.

### Mapping

Here is how we map numbers to be sent over the wire.

[0, 62] -> [65, 127] (`DF` not set)

1. Add 64 so that our `ttl` is high enough
2. Add 1 because we skipped 64

[63, 189] -> [129, 255] (`DF` not set)

1. Add 65 for the reasons above
2. Add 1 because we skipped 128

[190, 259] -> [65, 134] (`DF` set)

1. Subtract 128 because we need to map the `ttl` like in the first case
2. Add 2 because we skipped 64, 128
3. Add 1 because we skip 64 again
4. Set the `DF` flag in order to flip the 9th bit.

Factoring in the `DF` flag as the 9th bit, [190, 259] maps to [321, 390]

Run a ping command with the `ttl` as the number value, and set the `DF` flag accordingly. Reverse these operations on the other side and we receive the original number.

### Magic Numbers

We take advantage of the fact that we have a range greater than a byte to define some Magic Numbers. These signal things about the state of our program.

- Begin = 256

Signals that the server is to begin listening and interpreting pings.

- Take Filename = 257

Signals that the server is to begin taking the destination filename

- End Filename = 258

The server is to stop taking the filename and start listening for file content

- Finish = 259

Signals that the client is finished and the server should stop listening except for the Begin magic number