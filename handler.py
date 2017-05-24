# -*- coding: utf-8 -*-

import json
import re

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
    "live": {
        "_C_SERVER": "https://c.gamefestival365.co.kr:9000",
        "_G_SERVER": "https://g.gamefestival365.co.kr:9100",
    },
}


def update_member_info(envName=str, gameRegId=str, gameAccessId=None, gUserKey="", gScore=0):

    c = conn.cursor()

    # if user exists
    c.execute("SELECT count(*) AS total FROM users WHERE envName = ? and gameRegId=?", (envName, gameRegId,))
    user_count = c.fetchone()

    log.debug("users count: %s" % user_count)

    if user_count["total"] == 0:

        data = {
            "envName": envName,
            "gameRegId": gameRegId,
            "gameAccessId": gameAccessId,
            "gUserKey": gUserKey,
            "gScore": gScore
        }

        # Insert new user
        sql = "INSERT INTO users " \
              " (envName, gameRegId, gameAccessId, gUserKey, gSumScore) " \
              " VALUES " \
              "('%(envName)s', '%(gameRegId)s','%(gameAccessId)s','%(gUserKey)s', %(gScore)d )"

        log.debug(sql % data)
        c.execute(sql % data)
        conn.commit()

    if gameAccessId is not None:
        sql = " Update users set gameAccessId = ? where envName = ? and gameRegId = ?"
        c.execute(sql, (gameAccessId, envName, gameRegId,))
        conn.commit()

    if gUserKey is not None:
        sql = "Update users set gUserKey = ? where envName = ? and gameRegId = ?"
        c.execute(sql, (gUserKey, envName, gameRegId,))
        conn.commit()

    if gScore > 0:
        sql = " Update users set gSumScore = gSumScore + ? where envName = ? and gameRegId = ?"
        c.execute(sql, (gScore, envName, gameRegId,))
        conn.commit()


def get_member_info(environment=str, gfregid=str):

    conn.row_factory = dict_factory
    c = conn.cursor()

    # if user exists
    c.execute('SELECT * FROM users WHERE envName = ? and gameRegId=?', (environment, gfregid,))
    ret = c.fetchone()

    log.debug('member ret: %s' % ret)

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
        self.envName = None
        self.gameRegId = None
        self.userinfo = dict

    @asynchronous
    def prepare(self):

        path = re.search(r'/(?P<env_name>\w+)/(.*)/v2/(?P<gf365_game_reg_id>\w+)', self.request.path)
        env_name = path.group('env_name')
        gf365_game_reg_id = path.group('gf365_game_reg_id')

        if env_name not in _SERVER_INFO.keys():
            self.write_message(code="999", message="Unknown environment name: %s" % env_name)
            return
        else:
            self.envName = env_name

        if gf365_game_reg_id != "":
            self.gameRegId = str(gf365_game_reg_id)
            update_member_info(envName=self.envName, gameRegId=self.gameRegId)

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_message(self, code=str, message=None, item=None):
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
    def get(self, env_name=str, gf365_game_reg_id=str):
        self.post(env_name, gf365_game_reg_id)

    @asynchronous
    def post(self, env_name=str, gf365_game_reg_id=str):

        log.debug("Received login API")

        log.debug("env_name: %s" % env_name)
        log.debug("gf365_game_reg_id: %s" % gf365_game_reg_id)

        self.gameRegId = str(gf365_game_reg_id)
        update_member_info(envName=self.envName, gameRegId=self.gameRegId)

        url = "%s/games/v2/user/login" % _SERVER_INFO[self.envName]["_G_SERVER"]
        body = {
            "kind": "user#login",
            "gameRegId": self.gameRegId,
            "gameLoginTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "gUserKey": ""
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
            response_body = json.loads(response.body)

            data["retCode"] = response_body["retCode"]
            data["message"] = "OK"
            data["items"] = {
                "gameAccessId": response_body["item"]["gameAccessId"],
                "gameRegId": self.gameRegId
            }

            # if got success
            if response_body["retCode"] == "000":
                update_member_info(envName=self.envName,
                                   gameRegId=self.gameRegId,
                                   gameAccessId=response_body["item"]["gameAccessId"])

        self.write_message_by_data(data)
        return


class GFJoinHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    @asynchronous
    def get(self, env_name=str, gf365_game_reg_id=str):
        self.post(env_name, gf365_game_reg_id)

    @asynchronous
    def post(self, env_name=str, gf365_game_reg_id=str):

        log.debug("Received Join API")

        self.userinfo = get_member_info(environment=self.envName, gfregid=self.gameRegId)

        log.debug("Members: %s" % self.userinfo)

        if self.userinfo is None:
            self.write_message(code="999", message="need to login (no userinfo)")
            return

        if self.userinfo["gameAccessId"] is None:
            self.write_message(code="998", message="need to login (no accessid)")
            return

        url = "%s/games/v2/user/join" % _SERVER_INFO[self.envName]["_G_SERVER"]
        self.gameRegId = str(gf365_game_reg_id)
        update_member_info(envName=self.envName, gameRegId=self.gameRegId)

        body = {
            "kind": "user#join",
            "gameAccessId": self.userinfo["gameAccessId"],
            "gUserKey": self.userinfo["gUserKey"]
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=json.dumps(body), validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        if response.code == 200:

            response_body = json.loads(response.body)

            self.write_message(code=response_body["retCode"],
                               message=response_body["message"])
        else:
            self.write_message(code="999",
                               message="http error: %s" % response.code)


class ScoreHandler(BaseHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def get(self, env_name=str, gf365_game_reg_id=str):
        self.write_message(code="999", message="method error")
        return

    @asynchronous
    def post(self, env_name=str, gf365_game_reg_id=str):

        log.debug("Received score API")
        url = "%s/games/v2/score" % _SERVER_INFO[env_name]["_G_SERVER"]

        requested_body = None
        try:
            requested_body = json.loads(self.request.body)
            log.debug("requested_body: %s" % requested_body)
        except ValueError as e:
            log.debug("request.body: %s" % self.request.body)
            self.write_message(code="999", message="json syntax error")
            return

        self.gameRegId = gf365_game_reg_id
        self.userinfo = get_member_info(environment=env_name, gfregid=self.gameRegId)

        log.debug("Members: %s" % self.userinfo)

        if self.userinfo is None:
            self.write_message(code="999", message="need to login")
            return

        if self.userinfo["gameAccessId"] is None:
            self.write_message(code="998", message="need to login (no accessid)")
            return

        if "ScoreId" not in requested_body:
            self.write_message(code="899", message="missing ScoreId attribute")
            return

        ScoreId = str(requested_body["ScoreId"])

        if ScoreId not in ScoreData:
            self.write_message(code="998", message="unknown ScoreId: %s" % ScoreId)
            return

        body = {
            "kind": "score#write",
            "gameAccessId": self.userinfo["gameAccessId"],
            "gEvtTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "gScoreType": "wanna_be_1st",
            "gScore": int(ScoreData[ScoreId]),
            "gUserKey": "",
            "gServerId": 100
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", body=json.dumps(body), validate_cert=False)

        http_client.fetch(http_request, callback=self.on_fetch)

    def on_fetch(self, response=HTTPResponse):
        log.debug("response: %s" % response)
        log.debug("body: %s" % response.body)

        if response.code == 200:
            response_body = json.loads(response.body)

            self.write_message(code=response_body["retCode"],
                               message=response_body["message"])
        else:
            self.write_message(code="999",
                               message="http error: %s" % response.code)


class VersionHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    @asynchronous
    def prepare(self):
        log.debug("received get version")
        self.write("version %s" % "v2.0")
        self.finish()
