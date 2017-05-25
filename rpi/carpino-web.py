#!/usr/bin/env python
#
# Author:	Georgi Kolev
# Name:		carpino-web
# Version:	0.99c
#

import os
import json
from time import time
from subprocess import PIPE
from procname import setprocname
from tornado.process import Subprocess
from tornado import websocket, web, ioloop, gen

__version__ = '0.99c'
__license__ = 'GPLv3'
__author__ = 'Georgi.Kolev<at>gmail.com'


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            cl.append(self)

    def on_message(self, message):
        for c in cl:
            c.write_message(message)

    def on_close(self):
        if self in cl:
            cl.remove(self)


class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        mpd_commands = ['prev', 'next', 'play', 'stop']
        try:
            id = self.get_argument("id")
            value = self.get_argument("value")
            data = {"id": id, "value": value}
            data = json.dumps(data)
            for c in cl:
                c.write_message(data)
            if (id == 'mpd') and (value in mpd_commands):
                run_command('/usr/bin/mpc %s' % value)
        except:
            print 'MSG Error'
        self.redirect('/', permanent=True)
        # self.finish()

    @web.asynchronous
    def post(self): pass


@gen.coroutine
def run_command(command):
    process = Subprocess([command], stdout=PIPE, stderr=PIPE, shell=True)
    yield process.wait_for_exit()  # Waits without blocking
    out, err = process.stdout.read(), process.stderr.read()


# Set process name
setprocname('carpino_web')

cl = []
settings = {
    "static_path": os.path.join('/opt/carpino/', "static"),
}

app = web.Application([
    (r'/', IndexHandler),
    (r'/api', ApiHandler),
    (r'/ws', SocketHandler),
    (r'/(.*).js', web.StaticFileHandler, dict(path=settings['static_path'])),
    (r'/(.*).css', web.StaticFileHandler, dict(path=settings['static_path'])),
    (r'/(.*).map', web.StaticFileHandler, dict(path=settings['static_path'])),
], **settings)

if __name__ == '__main__':
    app.listen(7350)
    ioloop.IOLoop.instance().start()
# eof
