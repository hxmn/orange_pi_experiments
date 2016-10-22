#!/usr/bin/env python
# encoding: utf-8
import os
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import uuid
from time import time
from tornado.log import app_log as log
from tornado.options import define, options

from wsrpc import WebSocketRoute, WebSocket, wsrpc_static

define("listen", default='0.0.0.0', help="run on the given host")
define("port", default=9090, help="run on the given port", type=int)
define("pool_size", default=50, help="Default threadpool size", type=int)
define("debug", default=False, help="Debug", type=bool)
define("gzip", default=True, help="GZIP responses", type=bool)

COOKIE_SECRET = str(uuid.uuid4())


class Application(tornado.web.Application):
    def __init__(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        handlers = (
            wsrpc_static(r'/js/(.*)'),
            (r"/ws/", WebSocket),
            (r'/(.*)', tornado.web.StaticFileHandler, {
                'path': os.path.join(project_root, 'static'),
                'default_filename': 'index.html'
            }),
        )

        tornado.web.Application.__init__(
            self,
            handlers,
            xsrf_cookies=False,
            cookie_secret=COOKIE_SECRET,
            debug=options.debug,
            reload=options.debug,
            gzip=options.gzip,
        )


class TestRoute(WebSocketRoute):
    def init(self, **kwargs):
        return kwargs

    @tornado.gen.coroutine
    def delayed(self, delay=0):
        future = tornado.gen.Future()
        tornado.ioloop.IOLoop.instance().call_later(delay, lambda: future.set_result(True))
        yield future
        raise tornado.gen.Return("I'm delayed {0} seconds".format(delay))

    def getEpoch(self):
        return time()

    def requiredArgument(self, myarg):
        return True

    def _secure_method(self):
        return 'WTF???'

    @tornado.gen.coroutine
    def time(self, *args, **kwargs):
        for i in range(0, 10000):
            yield self.socket.call('print', a='hello %04d' % i)

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")

WebSocket.ROUTES['test'] = TestRoute


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address=options.listen)
    log.info('Server started {host}:{port}'.format(host=options.listen, port=options.port))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    exit(main())
else:
    application = tornado.wsgi.WSGIAdapter(Application())
