#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import json
import pprint
import time
from typing import Callable

import requests

from etpclient.etp.requester import *
from etpclient.rest_client import get_token_from_config
from etpclient.server_config import *
from etpclient.websocket_manager import WebSocketManager

pretty_p = pprint.PrettyPrinter(width=80)  # , compact=True)


def helper():
    print("############")
    print("#  HELPER  #")
    print("############")
    print(
        """[XXX] : replace XXX with your value
[XXX=Y] : replace XXX with your value, default is Y
[[XXX]] : optional parameter

[URI] for dataspaces can sometimes be set as "eml:///dataspace('DATASPACE_NAME')" but also with only the DATASPACE_NAME.

    Help : show this menu

    Quit : hard quit (no CloseSession sent)
    CloseSession : close this session

    Authorize             [ [TOKEN] | ( [USERNAME] [PASSWORD]) ]
    RequestSession

    GetDataArrayMetadata  [URI] [PATH_IN_RESOURCE]
    GetDataArray          [URI] [PATH_IN_RESOURCE]
    GetDataSubArray       [URI] [PATH_IN_RESOURCE] [START] [COUNT]
    PutDataArray          [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH] [[UUIDS]]*
    PutDataArray_filter   [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH] [[REGEX_TYPE_FILTER]]

    GetDataObject         [URI_1] [...] [URI_N]
    DeleteDataObjects     [URI_1] [...] [URI_N]
    PutDataObject         [FILE_PATH] [[DATASPACE_NAME]] [[UUIDS]]*

    GetResources          [[uri=eml:/// or notUri=DataspaceName]] [[depth=1]] [[SCOPE]]
    GetDeletedResources   [[uri=eml:/// or notUri=DataspaceName]] [[DELETE_TIME_FILTER]] [[DATA_OBJECT_TYPES]]*

    GetDataspaces
    PutDataspace          [NAME]
    DeleteDataspace       [NAME]*

    Download              [OUTPUT_FILE_PATH] [DATASPACE_NAME]

    GetSupportedTypes     [URI] [[COUNT=True]] [[RETURN_EMPTY_TYPES=True]] [[SCOPE=Self]]
"""
    )


def wait_symbol(nb):
    if nb % 4 == 0:
        return "|"
    elif nb % 4 == 1:
        return "/"
    elif nb % 4 == 2:
        return "-"
    elif nb % 4 == 3:
        return "\\"


def get_verified_url(url: str, prefix: list[str] = ["http://", "https://"]):
    for p in prefix:
        if url.lower().startswith(p.lower()):
            return url

    return prefix[0] + url


def get_token(get_token_url: str):
    if get_token_url is not None:
        result = requests.post(get_verified_url(get_token_url))
        try:
            return result.json()["token"]
        except:
            print("=====", result.text)
            logging.error(result)
    return None


def end_message(reason: str = None):
    print("1) Bye bye")


def get_parser():
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--host",
    #     # required=True,
    #     default="localhost",
    #     type=str,
    #     help="[Required] Server host (e.g. localhost or ip like XXX.XXX.XXX.XXX)",
    # )
    # parser.add_argument(
    #     "--port", type=int, default=None, help="Server port"
    # )
    # parser.add_argument(
    #     "--sub-path",
    #     type=str,
    #     help='Server sub-path (e.g. "etp" for an url like : "geosiris.com/etp/")',
    # )
    # parser.add_argument(
    #     "--username", "-u", type=str, help="The user login"
    # )
    # parser.add_argument(
    #     "--password", "-p", type=str, help="The user password"
    # )
    # parser.add_argument(
    #     "--token-url", type=str, help="The server get token url"
    # )
    # parser.add_argument("--token", "-t", type=str, help="An access token")
    parser.add_argument(
        "--caps", type=List, help="print http capabilities"
    )
    return parser


def get_parser_downloader():
    parser = get_parser()
    parser.add_argument(
        "-f", "--filter", nargs="*", default=[], help="qualifiedType list to filter the objects to download"
    )
    return parser


async def client(
    run_func: Callable,
    config: ServerConfig,
    # serv_url=None,
    # serv_port=None,
    # serv_sub_path=None,
    # serv_username=None,
    # serv_password=None,
    # serv_get_token_url=None,
    # serv_token=None,
    server_capabilities=False,
):
    serv_uri = config.get(SERVER_URL)
    serv_token = config.get(SERVER_TOKEN)
    serv_username = config.get(SERVER_USERNAME)
    serv_password = config.get(SERVER_PASSWORD)

    print(f"serv_uri {serv_uri} serv_token {serv_token} serv_username {serv_username} serv_password {serv_password}")

    headers = {}
    if serv_token is not None:
        headers["Authorization"] = "Bearer " + serv_token
    elif serv_token is not None:
        headers["Authorization"] = basic_auth_encode(serv_username, serv_password)

    if server_capabilities:
        serv_uri_http = serv_uri.split("://")[-1]
        serv_uri_http_caps_version = serv_uri_http + ('/' if not serv_uri_http.endswith('/') else '') + ".well-known/etp-server-capabilities?GetVersions=true"
        serv_uri_http_caps_value = serv_uri_http + ('/' if not serv_uri_http.endswith('/') else '') + ".well-known/etp-server-capabilities?GetVersion=" + ETPConnection.SUB_PROTOCOL

        print("Trying to contact server '" + str(serv_uri) + "'")
        print(
            "======> SERVER CAPS Test if contains :",
            ETPConnection.SUB_PROTOCOL,
        )
        _url_caps = "http://" + serv_uri_http_caps_version
        print(f"Trying to reach : {_url_caps}")
        req_result = None
        try:
            req_result = requests.get(_url_caps, timeout=0.5, headers=headers)
            pretty_p.pprint(json.loads(req_result.text))
            # assert ETPConnection.SUB_PROTOCOL in json.loads(server_caps_list_txt)
        except:
            try:
                print(f"\tFailed, {req_result}, try with https: ")
                _url_caps = "https://" + serv_uri_http_caps_version
                req_result = requests.get(_url_caps, timeout=0.5, headers=headers)
                pretty_p.pprint(json.loads(req_result.text))
            except Exception as e:
                # print(e)
                print(f"req result: {req_result}")
                # raise e
                print("Failed to recover server caps version")

        print("======> SERVER CAPS :")
        _url_caps = "http://" + serv_uri_http_caps_value
        print(f"Trying to reach : {_url_caps}")
        try:
            req_result = requests.get(_url_caps, timeout=0.5, headers=headers)
            pretty_p.pprint(json.loads(req_result.text))
            print("<====== SERVER CAPS\n")
        except:
            try:
                print(f"\tFailed, {req_result} try with https:")
                _url_caps = "https://" + serv_uri_http_caps_value
                req_result = requests.get(_url_caps, timeout=0.5, headers=headers)
                pretty_p.pprint(json.loads(req_result.text))
            except Exception as e:
                # print(e)
                print(f"req result: {req_result}")
                # raise e
                print("Failed to recover server caps version")

    serv_uri_ws = serv_uri
    if "://" not in serv_uri_ws:
        serv_uri_ws = "ws://" + serv_uri

    wsm = WebSocketManager(
        serv_uri_ws,
        username=serv_username,
        password=serv_password,
        token=serv_token or get_token_from_config(config),
        additional_headers={} or config.get_headers()
    )

    cpt_wait = 0
    time_step = 0.01
    while (
        not wsm.is_connected()
        and not wsm.closed
        and (cpt_wait * time_step < 30)
    ):
        if (cpt_wait * 1000 % 1000) < 2:
            print(f"\rwait for connection {wait_symbol(cpt_wait)}", end="")
        cpt_wait = cpt_wait + 1
        time.sleep(time_step)

    running = wsm.is_connected()

    if not running and (cpt_wait * time_step >= 30):
        print("Timeout...")

    result = None
    print(f"run func {run_func} running {running} wsm {wsm.is_connected()} {wsm.closed}")

    while running:
        running = await run_func(wsm)
        if not wsm.is_connected():
            running = False

    end_message()
