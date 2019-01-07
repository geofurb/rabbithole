#!/usr/bin/python3

"""CGI script for printing an endless stream of random ASCII characters

This script expects a SIGTERM from the server when it attempts a write after
the client has closed the connection. It will also try to catch the broken
pipe. If neither signal arrives, the server will need to use SIGKILL, or the
script will continue indefinitely. (Apache's mod_cgi applies SIGPIPE, SIGTERM,
and then SIGKILL. Thanks to Richard Harman @xabean for verifying this.) 

When run in the console, this script will print UTF-8 output; however, the
behavior when run as a CGI script is to print 7-bit ASCII characters, which
is the default behavior for Python stdout when piped.

As with any CGI script, remember to chmod 755 this so that it can be executed
by the webserver's worker and that your Python 3 binary has the appropriate
permissions. Log files must be writable by the worker groups, so chmod 666
those, too.

Take care to ensure that your webserver does not wait for the CGI process to
complete before returning the result, as the pipe will fill up and the process
will never return. (This is the case for python's http.server, which you may
have been thinking about using for testing purposes.)
"""

import time, datetime
import os, sys, signal
from random import seed, randint
import logging, cgitb


###################
## Configuration ##
###################

BITRATE = 500 * 1024 ** 1   # Restrict output rate (bits per second)
CHARACTERS_PER_LINE = 80    # Output is line-buffered, this sets line lengths

USE_CONTROL_CHARS = False       # Don't do this. Why would you do this? Don't.
USE_EXTENDED_CHARSET = False    # More entropy per bit sent, less compatible

ACCESS_LOGPATH = '../../logs/junkstream_log.txt'  # Log access here
ERROR_LOGPATH = '../../logs/'  # Log cgitb errors here


####################
## Initialization ##
####################

# Time how long the user is connected
start_time = time.time()

# Configure access logging
logging.basicConfig(
    filename=ACCESS_LOGPATH,
    level=logging.INFO,
    format='%(asctime)s - %(process)d %(levelname)s - %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S %z')

# Init CGI logging
cgitb.enable(display=0, logdir=ERROR_LOGPATH, format='text')

# Set SIGTERM to raise a TimeoutError so we can exit gracefully
def handler(signum, frame) :
    raise TimeoutError
signal.signal(signal.SIGTERM, handler)
proper_terminations = {TimeoutError, ConnectionResetError, BrokenPipeError}

# IP of the client receiving our stream
REMOTE_HOST_ADDR = os.environ.get('REMOTE_ADDR', default='255.255.255.255')
# Resource the client requested
URL_REQUESTED = os.environ.get('REQUEST_URI', default='http://???')
# Method (GET/POST)
REQUEST_METHOD = os.environ.get('REQUEST_METHOD', default='(GET?)')
# User Agent
USER_AGENT = os.environ.get('HTTP_USER_AGENT', default='(user-agent?)')

# Sleep up to this amount between blurts
wait_time = (7 * CHARACTERS_PER_LINE) / BITRATE
# We just need a list of the right length so we can do a list comprehension
linerange = range(CHARACTERS_PER_LINE)
# Some fine determinism gives structure to our output ;)
seed(1137)
# Configure character ranges
charmin = 0 if USE_CONTROL_CHARS else 32
charmax = 128 if USE_EXTENDED_CHARSET else 80

# Log the visitor
logging.info(' - '.join([
    f'CONNECTED: {REMOTE_HOST_ADDR}',
    f'{REQUEST_METHOD} {URL_REQUESTED}',
    f'"{USER_AGENT}\"']))


###############
## Execution ##
###############

# Mandatory HTTP headers
print('Content-type: text/plain; charset=ASCII-8BIT')
STRING_ENCODING = 'ascii'           # Should match charset
print('Transfer-Encoding: chunked') # Necessary to stream the "data"
print()                             # Empty line marks the end of CGI headers

bytes_sent = 0
try :
    while True :
        t_message_start = time.time()
        line = "".join([chr(randint(charmin, charmax)) for x in linerange])
        msg_length = len(line.encode(STRING_ENCODING))
        bytes_sent += msg_length
        print(f'{msg_length:x}\r\n{line}',end='\r\n',flush=True)
        time.sleep(max([0,
                        t_message_start - time.time() + msg_length*8/BITRATE]))
except Exception as e:    
    # Log the original error if not an expected exit path
    if e not in proper_terminations:
        logging.error('Unhandled exception in stream!', exc_info=True)
    try:
        # Log the time the connection lasted and total bytes transferred
        bytes_sent /= 1024
        tx_units = 'kB'
        if bytes_sent > (1024 ** 2) :
            bytes_sent /= (1024 ** 2)
            tx_units = 'GB'
        elif bytes_sent > (1024 * 10) :
            bytes_sent /= 1024
            tx_units = 'MB'
        conn_time = str(datetime.timedelta(seconds=time.time() - start_time))
        logging.info(' - '.join([
            f'DISCONNECTED: {REMOTE_HOST_ADDR}',
            f'{bytes_sent:.2f} {tx_units} over {conn_time}']))
        # If this wasn't an expected interruption, raise the error
        if e in proper_terminations:
            sys.exit(0)         # We always knew it would end like this
        else:
            raise Exception     # It was never supposed to go like this
    except:
        sys.exit(1)
