# Inspired by: http://emptysquare.net/blog/pausing-with-tornado/
# Test with:
# ab -c 10 -n 10 "http://localhost:8888/"

import time
import tornado.web
import tornado.httpclient
from tornado.ioloop import IOLoop
from tornado import gen

import logging

from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(4)

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        self.write("Going to sleep...")
        logging.warning("going to sleep.")
        # Note that nothing is written to the client until `finish` is called!
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + 5)
        self.write("I'm awake!")
        logging.warning("awake")
        self.finish()
        # or use `self.render` that calls `finish` itself
        # See http://www.tornadoweb.org/documentation/_modules/tornado/web.html#RequestHandler.render


class SimpleHandler(tornado.web.RequestHandler):

    @gen.coroutine
    def get(self):
        self.write("Going to sleep...")
        logging.warning("going to sleep.")
        yield thread_pool.submit(self.my_function)

    def my_function(self):

        http_client = tornado.httpclient.AsyncHTTPClient()
        response = http_client.fetch("https://works.gamefestival365.co.kr:9000/login/game/token",
                                     validate_cert=False)
        self.write("get response: %s" % response)
        logging.warning("awake")


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/simple", SimpleHandler),
    ])


if __name__ == "__main__":
    application.listen(8890)
    IOLoop.instance().start()