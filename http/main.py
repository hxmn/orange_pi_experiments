#!/usr/bin/env python
# encoding: utf-8
import os
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import uuid
from random import randint
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
    JOKES = [
        '[ $[ $RANDOM % 6 ] == 0 ] && rm -rf / || echo *Click*',
        'It’s always a long day, 86,400 won’t fit into a short.',
        'Programming is like sex:\nOne mistake and you have to support it for the rest of your life.',
        'There are three kinds of lies: lies, damned lies, and benchmarks.',
        'The generation of random numbers is too important to be left to chance.',
        'A SQL query goes to a restaurant, walks up to 2 tables and says “Can I join you”?',
    ]

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

    def exc(self):
        raise Exception(u"Test Тест テスト 测试")

    @tornado.gen.coroutine
    def getJoke(self):
        joke = self.JOKES[randint(0, len(self.JOKES) - 1)]
        result = yield self.socket.call('joke', joke=joke)
        log.info('Client said that was "{0}"'.format('awesome' if result else 'awful'))
        yield self.socket.call('print', result='Cool' if result else 'Hmm.. Try again.')
        raise tornado.gen.Return("Ok.")


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
    try:
        from google.appengine.ext import vendor

        vendor.add('lib')

    except ImportError:
        pass

    application = tornado.wsgi.WSGIAdapter(Application())
