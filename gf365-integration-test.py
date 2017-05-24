#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import sched, time

from tornado.httpclient import HTTPResponse, HTTPRequest, HTTPClient
from datetime import datetime

# simple logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('gf365')
formatter = logging.Formatter('%(asctime)s, %(levelname)s - %(name)s - [%(filename)s:%(lineno)d], %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

gf_gameid = 4
gf_gameRegId = "G0140042113321"
gf_AccessId = ""
gf_gUserkey = "tpm0013@gcon.kr"


def get_accessId(gameRegId=str):
    url = "https://works-g.gamefestival365.co.kr:9100/games/v2/user/login"
    body = {
        "kind": "user#login",
        "gameRegId": gameRegId,
        "gameLoginTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
        "gUserKey": gf_gUserkey
    }

    body_value = json.dumps(body)
    logger.debug("body: %s" % body_value)

    http_client = HTTPClient()
    http_request = HTTPRequest(url, method="POST", body=body_value, validate_cert=False)

    response = http_client.fetch(http_request)

    logger.debug("response: %s" % response)
    # logger.debug("body: %s" % response.body)

    if response.code == 200:
        logger.debug("response_body: %s" % response.body)

        response_body = json.loads(response.body)

        # if got success
        if response_body["retCode"] != "000":
            logger.debug("login error: %s" % gf_gameRegId)
            return ""

        else:
            return response_body["item"]["gameAccessId"]


def join_gf365(gameAccessId=str):
    url = "https://works-g.gamefestival365.co.kr:9100/games/v2/user/join"
    body = {
        "kind": "user#join",
        "gameAccessId": gameAccessId,
        "gUserKey": gf_gUserkey
    }

    body_value = json.dumps(body)
    logger.debug("body: %s" % body_value)

    http_client = HTTPClient()
    http_request = HTTPRequest(url, method="POST", body=body_value, validate_cert=False)

    response = http_client.fetch(http_request)

    logger.debug("response join_gf365: %s" % response.body)
    # logger.debug("body: %s" % response.body)

    return


def send_score(gameAccessId=str, score=0):

    url = "https://works-g.gamefestival365.co.kr:9100/games/v2/score"
    body = {
        "kind": "score#write",
        "gameAccessId": gameAccessId,
        "gEvtTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
        "gScoreType": "wanna_be_1st",
        "gScore": score,
        "gUserKey": gf_gUserkey,
        "gServerId": 100
    }

    body_value = json.dumps(body)
    logger.debug("body: %s" % body_value)

    http_client = HTTPClient()
    http_request = HTTPRequest(url, method="POST", body=body_value, validate_cert=False)

    response = http_client.fetch(http_request)

    logger.debug("response: %s" % response)
    logger.debug("body: %s" % response.body)

    return response


if __name__ == "__main__":

    starttime=time.time()
    AccessId = get_accessId(gameRegId=gf_gameRegId)

    logger.debug("gf AccessId: %s" % AccessId)

    join_gf365(AccessId)

    deltascore = 100

    if AccessId == "":
        exit(0)

    while(True):

        time.sleep(10.0)

        response = send_score(gameAccessId=AccessId, score=deltascore)

        if response.code == 200:
            logger.debug("response_body: %s" % response.body)
            response_body = json.loads(response.body)

            response_body_buff = json.loads(response.body)

            if type(response_body_buff) is list:
                response_body = response_body_buff[0]
            else:
                response_body = response_body_buff

            logger.debug("response_body: %s" % response_body)

    # if len(sys.argv) != 3:
    #     print('Usage: gameserver --env=<environment name> --port=<port number>')
    # else:
    #     main()

