# -*- coding: utf-8 -*-

import json

from tornado.httpclient import AsyncHTTPClient, HTTPResponse, HTTPRequest
from tornado.web import asynchronous, RequestHandler
from library.logger import log
from datetime import datetime

from library.sqlitedb import conn, dict_factory

ScoreData = {
    "K100": 100,
    "K300": 300,
    "K500": 500,
    "K700": 700,
    "K1000": 1000,
}

_SERVER_INFO = {
    "works": {
        "_C_SERVER": "https://works-c.gamefestival365.co.kr:9000",
        "_G_SERVER": "https://works-g.gamefestival365.co.kr:9100"
    },
    "dev": {
        "_C_SERVER": "http://172.20.101.8:9000",
        "_G_SERVER": "http://172.20.101.8:9100"
    },
    "qa": {
        "_C_SERVER": "http://172.20.102.3:9000",
        "_G_SERVER": "http://172.20.102.3:9100"
    },
    "stage": {
        "_C_SERVER": "http://211.253.14.199:9000",
        "_G_SERVER": "http://211.253.25.51:9100"
    },
}

_ENV = "qa"
_C_SERVER = _SERVER_INFO[_ENV]["_C_SERVER"]
_G_SERVER = _SERVER_INFO[_ENV]["_G_SERVER"]


def UpdateMember(evtToken=str, evtAuthToken=None,
                 missionToken=None, gUserKey="", gScore=0):

    c = conn.cursor()

    # if user exists
    c.execute("SELECT count(*) AS total FROM users WHERE evtToken=?", (evtToken,))
    user_count = c.fetchone()

    log.debug("users count: %s" % user_count)

    if user_count["total"] == 0:

        data = {
            "evtToken": evtToken,
            "evtAuthToken": evtAuthToken,
            "missionToken": missionToken,
            "gUserKey": gUserKey,
            "gSumScore": gScore
        }

        # Insert new user
        sql = "INSERT INTO users " \
              " (evtToken, evtAuthToken, missionToken, gUserKey, gSumScore) " \
              " VALUES " \
              "('%(evtToken)s','%(evtAuthToken)s','%(missionToken)s','%(gUserKey)s', %(gSumScore)d )"

        log.debug(sql % data)
        c.execute(sql % data)

        conn.commit()

    if evtAuthToken != None:

        sql = " Update users set evtAuthToken = ? where evtToken = ?"
        c.execute(sql, (evtAuthToken, evtToken,))
        conn.commit()

    if missionToken != None:
        sql = " Update users set missionToken = ? where evtToken = ?"
        c.execute(sql, (missionToken, evtToken,))
        conn.commit()

    if gUserKey != None:
        sql = "Update users set gUserKey = ? where evtToken = ?"
        c.execute(sql, (gUserKey, evtToken,))
        conn.commit()

    if gScore > 0:
        sql = " Update users set gSumScore = gSumScore + ? where evtToken = ?"
        c.execute(sql, (gScore, evtToken,))
        conn.commit()


def SelectMember(evtToken=str):

    conn.row_factory = dict_factory
    c = conn.cursor()

    # if user exists
    c.execute('SELECT * FROM users WHERE evtToken=?', (evtToken,))
    ret = c.fetchone()

    # result = {
    #     "evtToken": str(ret["evtToken"]),
    #     "evtAuthToken": str(ret["evtAuthToken"]),
    #     "missionToken": str(ret["missionToken"]),
    #     "gUserKey": str(ret["gUserKey"]),
    #     "gSumScore": int(ret["gSumScore"]),
    # }

    return ret


class BaseHandler(RequestHandler):

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.evtToken = None
        self.userinfo = dict

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
        self.finish()
        self.clear()
        return

    def write_message_by_data(self, data=dict):

        self.write_message(code=data['retCode'],
                           message=data['message'],
                           item=data['items'])


class GFLoginHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self, etoken=str):

        self.evtToken = str(etoken)

        UpdateMember(evtToken=self.evtToken)

        url = "%s/login/game/v2/%s" % (_C_SERVER, str(self.evtToken))
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

            data["retCode"] = response_body["retCode"]
            data["message"] = "OK"
            data["items"] = {
                "evtAuthToken": response_body["evtAuthToken"],
                "evtEndTime": response_body["evtEndTime"]
            }

            # if got success
            if response_body["retCode"] == "000":
                UpdateMember(evtToken=self.evtToken,
                             evtAuthToken=response_body["evtAuthToken"])

        self.write_message_by_data(data)


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
        url = "%s/score/v2/%d" % (_G_SERVER, int(serverIndex))

        requested_body = None
        try:
            requested_body = json.loads(self.request.body)
            log.debug("requested_body: %s" % requested_body)
        except ValueError as e:
            log.debug("request.body: %s" % self.request.body)
            self.write_message(code="999", message="json syntax error")

        self.evtToken = str(requested_body["evtToken"])
        self.userinfo = SelectMember(self.evtToken)

        log.debug("Members: %s" % self.userinfo)

        if self.userinfo["evtToken"] != self.evtToken:
            self.write_message(code="999", message="need to login")

        if self.userinfo["evtAuthToken"] is None:
            self.write_message(code="999", message="need to login")

        if "ScoreId" not in requested_body:
            self.write_message(code="998", message="missing ScoreId attribute")

        ScoreId = str(requested_body["ScoreId"])

        if ScoreId not in ScoreData:
            self.write_message(code="998", message="unknown ScoreId: %s" % ScoreId)

        deltaScore = int(ScoreData[ScoreId])

        body = {
            "kind": "score#write",
            "gameId": 90001,
            "eventId": 91001,
            "evtToken": self.evtToken,
            "evtAuthToken": self.userinfo["evtAuthToken"],
            "gEvtTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "gSumScore": self.userinfo["gSumScore"] + deltaScore,
            "gDeltaScore": deltaScore,
            "gScoreType": ScoreId,
            "gUserKey": self.userinfo["gUserKey"]
        }

        body_value = json.dumps(body)
        log.debug("body: %s" % body_value)
        self.score = deltaScore

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
                UpdateMember(evtToken=self.evtToken, gScore=self.score)

            item = {
                "evtToken": self.evtToken,
                "evtAuthToken": self.userinfo["evtAuthToken"],
                "gSumScore": self.userinfo["gSumScore"]
            }

            self.write_message(code=response_body["retCode"],
                               message=response_body["message"],
                               item=item)
        else:
            self.write_message(code="999",
                               message="http error: %s" % response.code)


class MissionInfoHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self, evtToken):

        self.evtToken = str(evtToken)
        self.userinfo = SelectMember(self.evtToken)

        log.debug("Members: %s" % self.userinfo)

        if self.userinfo is None:
            self.write_message(code="999", message="need to login (none info)")

        if self.userinfo["evtAuthToken"] is None:
            self.write_message(code="998", message="need to login (none authtoken)")

        url = "%s/mission/getinfo/v1/100" % _G_SERVER
        body = {
            "kind": "mission#getinfo",
            "evtToken": self.userinfo["evtToken"],
            "evtAuthToken": self.userinfo["evtAuthToken"],
            "gUserKey": "userkey"
        }

        log.debug("request url: %s" % url)
        log.debug("request body: %s" % body)

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=json.dumps(body), validate_cert=False)

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

            if response.body == "":
                self.write_message(code="999", message="unknown api error. (response null from api)")

            response_body_buff = json.loads(response.body)
            response_body = response_body_buff[0]

            if response_body["retCode"] != "000":
                data["retCode"] = response_body["retCode"]
                data["message"] = response_body["message"]
                data["items"] = response_body["item"]

            else:
                data["retCode"] = response_body["retCode"]
                data["message"] = "OK"
                data["items"] = {
                    "evtAuthToken": response_body["evtAuthToken"],
                    "evtEndTime": response_body["evtEndTime"],
                    "missiontoken": str(response_body["item"]["missiontoken"]),
                    "missiondetailindex": int(response_body["item"]["missiondetailindex"]),
                    "missionlimittime": str(response_body["item"]["missionlimittime"]),
                    "missionScore": int(response_body["item"]["missionScore"]),
                    "lefttime": int(response_body["item"]["lefttime"]),
                }

                UpdateMember(evtToken=self.evtToken,
                             missionToken=str(response_body["item"]["missiontoken"]))

        self.write_message_by_data(data)


class MissionEndHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def get(self, *args, **kwargs):
        self.write_message(code="899", message="not support get")

    @asynchronous
    def post(self, evtToken):

        url = "%s/mission/end" % _C_SERVER
        self.evtToken = str(evtToken)
        self.userinfo = SelectMember(self.evtToken)

        requested_body = None
        try:
            requested_body = json.loads(self.request.body)
            log.debug("requested_body: %s" % requested_body)
        except ValueError as e:
            log.debug("request.body: %s" % self.request.body)
            self.write_message(code="999", message="json syntax error")

        if self.userinfo is None:
            self.write_message(code="999", message="need to login (none info)")

        if "result" not in requested_body:
            self.write_message(code="998", message="missing ScoreId attribute")

        if self.userinfo["evtAuthToken"] is None:
            self.write_message(code="999", message="need to login")

        if self.userinfo["missionToken"] is None:
            self.write_message(code="999", message="none missionToken")

        mission_result = int(requested_body["result"])

        body = {
            "result": mission_result,
            "evtToken": self.userinfo["evtToken"],
            "evtAuthToken": self.userinfo["evtAuthToken"],
            "missionToken": self.userinfo["missionToken"],
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=json.dumps(body), validate_cert=False)

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

            if response.body == "":
                self.write_message(code="999", message="unknown api error. (response null from api)")

            response_body = json.loads(response.body)

            if response_body["code"] != "000":
                data["retCode"] = response_body["code"]
                data["message"] = ""
                data["items"] = ""

            else:
                data["retCode"] = response_body["code"]
                data["message"] = "OK"
                data["items"] = {
                    "missiontoken": self.userinfo["missionToken"],
                }

                UpdateMember(evtToken=self.evtToken,
                             missionToken=str(response_body["item"]["missiontoken"]))

        self.write_message_by_data(data)


class VersionHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def prepare(self):
        log.debug("get version")
        self.write("version %s" % "v9.9")
        self.finish()
