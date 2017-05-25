#!/usr/bin/env python
#
# Author:	Georgi Kolev
# Name:		carpino-can
# Version:	0.99f
#


import json
from can import CanMsg
from can import CarStatus
from mpd import MPDClient
from time import sleep
from Queue import Queue
from serial import Serial
from threading import Lock
from procname import setprocname
from thread import start_new_thread
from websocket import create_connection

__version__ = '0.99f'
__license__ = 'GPLv3'
__author__ = 'georgi.kolev<at>gmail.com'


class LockableMPDClient(MPDClient):
    def __init__(self, use_unicode=False):
        super(LockableMPDClient, self).__init__()
        self.use_unicode = use_unicode
        self._lock = Lock()

    def __exit__(self, type, value, traceback):
        self.release()

    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def __enter__(self):
        self.acquire()


def get_dname(cur_song):
    if ('artist' in cur_song) and ('title' in cur_song):
        cur_song = '%s - %s' \
            % (cur_song['artist'], cur_song['title'])
    else:
        cur_song = cur_song['file']
    return cur_song[:64].replace("'", "")


def get_track(mpdconn, csong='none'):
    with mpdconn:
        cur_song = mpdconn.currentsong()
        csong = 'track_name=' + get_dname(cur_song)
    return csong


def read_temp(tfpath='/sys/class/thermal/thermal_zone1/temp', tval=0):
    with open(tfpath) as f:
        tval = int(f.read())
    return 'cpu_temp='+str(tval)


def mpd_thread(mpd_queue, wsconn, mpdconn):
    while True:
        mpd_cmd = mpd_queue.get()
        try:
            if   mpd_cmd == 'next': mpdconn.next()
            elif mpd_cmd == 'prev': mpdconn.previous()
            elif mpd_cmd == 'play': mpdconn.play()
            elif mpd_cmd == 'stop': mpdconn.stop()
            else:
                print('mpd_thread: Unknown command.')
        except: pass  # Bad name?
        mpd_queue.task_done()

        # Sleep for 0.2s and clear queue
        # To avoid spawning multiple events
        sleep(0.2)
        while not mpd_queue.empty():
            try:
                _ = mpd_queue.get(0)
                mpd_queue.task_done()
            except:
                break


def status_thread(ws_conn, mpdconn):
    while True:
        # Send CPU Temp & Current track data to WS
        try:
            ws_conn.send(pack_data(read_temp()))
            ws_conn.send(pack_data(get_track(mpdconn)))
        except UnicodeDecodeError as e:
            pass
        # Keep mpd connection alive
        mpdconn.ping()
        sleep(3)


def pack_data(dt):
    dt = dt.split('=')
    dt = {u'id': dt[0], u'value': dt[1]}
    return json.dumps(dt)


def msg2str(m, s=''):
    for e in m:
        e = hex(e).replace('0x', '')
        s += fixlen(e, 2)
    return s


def fixlen(s, l):
    return str(s).rjust(l).replace(' ', '0')


def msg2str2(m, s=''):
    return ' '.join(map(hex, m))


# Queues
mpd_queue = Queue()
# Initialize CAN stuff
bmw = CarStatus(debug=True)
msg = CanMsg(debug=True)

# Lockable MPD Client
mpclient = LockableMPDClient()
mpclient.connect('localhost', 6600)

# Serial connection
ser = Serial('/dev/ttyUSB0', 115200)
ws = create_connection("ws://127.0.0.1:7350/ws")

# Start threads
start_new_thread(mpd_thread, (mpd_queue, ws, mpclient,))
start_new_thread(status_thread, (ws, mpclient,))

# Change process name
setprocname('carpino_can')

while True:
    buffer = ''
    buffer = ser.readline().strip()

    print buffer
    if msg.parse(buffer):         # Parse CAN message
        result = bmw.msg(msg)     # Read message
        if not result: continue   # Skip unknown/empty
        for res in result:
            if not res: continue  # Skip unknown/empty
            if res.startswith('mpd='):  # mpd commands
                mpd_queue.put(res.split('=')[-1])
                print 'putting'
            # Push data to WebSocket
            ws.send(pack_data(res))
# eof
