# check evtToken

import tornado.web
import tornado.httpclient
from tornado import gen
from concurrent.futures import ThreadPoolExecutor
from library.logger import log

thread_pool = ThreadPoolExecutor(4)


class CHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def post(self):

        log.debug("going to request.")
        api_url = "https://works.c.gamefestival365.co.kr:9000/login/game/token"
        # api_url = "https://www.hostedgraphite.com/app/"

        http_client = tornado.httpclient.AsyncHTTPClient()

        http_client.fetch(api_url, validate_cert=False, callback=self.on_fetch)
        # http_client.fetch(api_url, self.api_process, validate_cert=False)

    def on_fetch(self, response=tornado.httpclient.HTTPResponse):
        log.debug("response: %s" % response)

        if response.code != 200:
            self.write("http error: %s" % response)
        else:
            self.write(response.body)

        self.finish()


class GHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def post(self):
        log.debug("going to request.")
        api_url = "https://works.g.gamefestival365.co.kr:9100/score/v1/100"
        # api_url = "https://www.hostedgraphite.com/app/"

        http_client = tornado.httpclient.AsyncHTTPClient()

        http_client.fetch(api_url, validate_cert=False, callback=self.on_fetch)
        # http_client.fetch(api_url, self.api_process, validate_cert=False)

    def on_fetch(self, response=tornado.httpclient.HTTPResponse):
        log.debug("response: %s" % response)

        if response.code != 200:
            self.write("http error: %s" % response)
        else:
            self.write(response.body)

        self.finish()
