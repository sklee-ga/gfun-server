# -*- coding: utf-8 -*-

import json

from tornado.httpclient import AsyncHTTPClient, HTTPResponse, HTTPRequest
from tornado.web import asynchronous, RequestHandler
from library.logger import log
from datetime import datetime


Members = dict()


class BaseHandler(RequestHandler):

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.evtToken = None

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_message(self, code=None, message=None, item=None):
        response_body = {
            "retCode": code,
            "message": message,
            "items": item
        }

        output = json.dumps(response_body)
        self.write(output)

    def write_message_by_data(self, data=dict):
        response_body = {
            "retCode": data['retCode'],
            "message": data['message'],
            "items": data['items']
        }

        output = json.dumps(response_body)
        self.write(output)

    def update_member(self, evtToken=str, evtAuthToken=None,
                      missionToken=None, gUserKey="", gScore=0):

        if evtToken not in Members:
            Members[evtToken] = {
                "evtToken": evtToken,
                "evtAuthToken": evtAuthToken,
                "missionToken": missionToken,
                "gUserKey": gUserKey,
                "gSumScore": gScore
            }

        if evtAuthToken != None:
            Members[evtToken]["evtAuthToken"] = evtAuthToken

        if missionToken != None:
            Members[evtToken]["missionToken"] = missionToken

        if gUserKey != None:
            Members[evtToken]["gUserKey"] = gUserKey

        if gScore > 0:
            Members[evtToken]["gSumScore"] = Members[evtToken]["gSumScore"] + gScore


class GFLoginHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self, etoken=str):

        self.evtToken = str(etoken)

        self.update_member(evtToken=self.evtToken)

        url = "https://works-c.gamefestival365.co.kr:9000/login/game/%s" % str(self.evtToken)
        body = ""

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=body, validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)
        # http_client.fetch(api_url, self.api_process, validate_cert=False)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        data = {
            "retCode": 999,
            "message" ""
            "items": ""
        }

        if response.code == 200:
            response_body = json.loads(response.body)

            data["retCode"] = response_body["code"]
            data["message"] = "OK"
            data["items"] = {
                "evtAuthToken": response_body["evtAuthToken"],
                "evtEndTime": response_body["evtEndTime"]
            }

            # if got success
            if response_body["code"] == "000":
                self.update_member(evtToken=self.evtToken,
                                   evtAuthToken=response_body["evtAuthToken"])

        self.write_message_by_data(data)
        self.finish()


class ScoreHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super(ScoreHandler, self).__init__(application, request, **kwargs)
        self.evtToken = None
        self.score = 0

    @asynchronous
    def post(self, serverIndex):

        log.debug("Request GF365 score API")
        url = "https://works-g.gamefestival365.co.kr:9100/score/v2/%d" % int(serverIndex)

        requested_body = json.loads(self.request.body)
        log.debug("req: %s" % requested_body)
        self.evtToken = requested_body["evtToken"]

        if self.evtToken not in Members:
            self.write_message(code="999", message="need to login")
            self.finish()

        if Members[self.evtToken]["evtAuthToken"] is None:
            self.write_message(code="999", message="need to login")
            self.finish()

        if "Score" not in requested_body:
            self.write_message(code="998", message="missing Score attribute")
            self.finish()

        body = {
            "kind": "score#write",
            "gameId": 90001,
            "eventId": 91001,
            "evtToken": self.evtToken,
            "evtAuthToken": Members[self.evtToken]["evtAuthToken"],
            "gEvtTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "gSumScore": Members[self.evtToken]["gSumScore"] + int(requested_body["Score"]),
            "gDeltaScore": int(requested_body["Score"]),
            "gScoreType": "AAA100",
            "gUserKey": Members[self.evtToken]["gUserKey"]
        }

        body_value = json.dumps(body)
        self.score = int(requested_body["Score"])

        log.debug("body: %s" % body_value)

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=body_value, validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        if response.code == 200:
            response_body_buff = json.loads(response.body)

            if type(response_body_buff) is list:
                response_body = response_body_buff[0]
            else:
                response_body = response_body_buff

            log.debug("response_body: %s" % response_body)

            # if got success update member
            if response_body["retCode"] == "000":
                self.update_member(evtToken=self.evtToken,
                                   gScore=self.score)

            item = {
                "evtToken": self.evtToken,
                "evtAuthToken": Members[self.evtToken]["evtAuthToken"],
                "gSumScore": Members[self.evtToken]["gSumScore"]
            }

            self.write_message(code=response_body["retCode"],
                               message=response_body["message"],
                               item=item)
        else:
            self.write_message(code="999",
                               message="http error: %s" % response.code)

        self.finish()


class MissionInfoHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self, evtToken):

        url = "https://works-c.gamefestival365.co.kr:9000/login/game/%d" % int(evtToken)
        body = {
            "kind": "mission#getinfo",
            "evtToken": "33334343",
            "evtAuthToken": "94C323423423B5F4",
            "gUserKey": "userkey"
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=body, validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)
        # http_client.fetch(api_url, self.api_process, validate_cert=False)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        data = {
            "retCode": 999,
            "message" ""
            "items": ""
        }

        if response.code == 200:
            response_body = json.loads(response.body)

            data["retCode"] = response_body["code"]
            data["message"] = "OK"
            data["items"] = {
                "evtAuthToken": response_body["evtAuthToken"],
                "evtEndTime": response_body["evtEndTime"]
            }

        self.write_message_by_data(data)
        self.finish()


class MissionEndHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self, evtToken):

        url = "https://works-c.gamefestival365.co.kr:9000/login/game/%d" % int(evtToken)
        #// 미션 토큰 : 개발사 서버가 GAPI의 mission/getinfo 로 얻었던 미션토큰을 완료시에 보내줘야 한다
        body = {
            "missiontoken": "234234234"
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=body, validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)
        # http_client.fetch(api_url, self.api_process, validate_cert=False)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        data = {
            "retCode": 999,
            "message" ""
            "items": ""
        }

        if response.code == 200:
            response_body = json.loads(response.body)

            data["retCode"] = response_body["code"]
            data["message"] = "OK"
            data["items"] = {
                "evtAuthToken": response_body["evtAuthToken"],
                "evtEndTime": response_body["evtEndTime"]
            }

        self.write_message_by_data(data)
        self.finish()


class VersionHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def prepare(self):
        log.debug("get version")
        self.write("version %s" % "v9.9")

        self.finish()
