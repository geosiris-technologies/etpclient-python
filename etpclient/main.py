#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import requests
import asyncio
import time
import json
import argparse
import pprint

from etpproto.connection import ETPConnection

from etpclient.websocket_manager import WebSocketManager
from etpclient.etp.requester import *


pretty_p = pprint.PrettyPrinter(width=80)  # , compact=True)


def helper():
    print("############")
    print("#  HELPER  #")
    print("############")
    print("""[XXX] : replace XXX with your value
[XXX=Y] : replace XXX with your value, default is Y
[[XXX]] : optional parameter

\tHelp : show this menu

\tQuit : hard quit (no CloseSession sent)
\tCloseSession : close this session

\tGetDataArrayMetadata  [URI] [PATH_IN_RESOURCE] 
\tGetDataArray          [URI] [PATH_IN_RESOURCE] 
\tGetDataSubArray       [URI] [PATH_IN_RESOURCE] [START] [COUNT]
\tPutDataArray          [[UUIDS]]* [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH]

\tGetDataObject         [URI_1] [...] [URI_N]
\tPutDataObject         [FILE_PATH] [[DATASPACE_NAME]]
\tGetResources          [[uri=eml:/// or notUri=DataspaceName]] [[depth=1]] [[SCOPE]]

\tGetDataspaces
\tPutDataspace          [NAME]
\tDeleteDataspace       [NAME]
""")


def wait_symbol(nb):
    if nb % 4 == 0:
        return "|"
    elif nb % 4 == 1:
        return "/"
    elif nb % 4 == 2:
        return "-"
    elif nb % 4 == 3:
        return "\\"


def get_verified_url(url: str, prefix:list[str]=["http://", "https://"]):
    for p in prefix:
        if url.lower().startswith(p.lower()):
            return url

    return prefix[0] + url


def get_token(get_token_url: str):
    if get_token_url:
        return requests.get(get_verified_url(get_token_url)).json()["token"]
    return None

def end_message(reason: str = None):
    
    print("Bye bye")

async def client(
    serv_url=None,
    serv_port=None,
    serv_sub_path=None,
    serv_username=None,
    serv_password=None,
    serv_get_token_url=None,
):
    serv_uri = (
        str(serv_url)
        + (":" + str(serv_port) if serv_port else "")
        + "/"
        + (serv_sub_path + "/" if serv_sub_path else "")
    )

    print("Trying to contact server '" + str(serv_uri) + "'")
    print("======> SERVER CAPS Test if contains :", ETPConnection.SUB_PROTOCOL)
    server_caps_list_txt = requests.get(
        "http://"
        + serv_uri
        + ".well-known/etp-server-capabilities?GetVersions=true"
    ).text
    pretty_p.pprint(server_caps_list_txt)
    # assert ETPConnection.SUB_PROTOCOL in json.loads(server_caps_list_txt)

    print("======> SERVER CAPS :")
    server_caps_txt = requests.get(
        "http://"
        + serv_uri
        + ".well-known/etp-server-capabilities?GetVersion="
        + ETPConnection.SUB_PROTOCOL
    ).text
    pretty_p.pprint(json.loads(server_caps_txt))
    print("<====== SERVER CAPS\n")

    wsm = WebSocketManager("ws://" + serv_uri, username = serv_username, password = serv_password, token = get_token(serv_get_token_url))
    cpt_wait = 0
    time_step = 0.01
    while not wsm.is_connected() and (cpt_wait * time_step < 30):
        if (cpt_wait * 1000 % 1000) < 5 :
            print("\rwait for connection" + wait_symbol(cpt_wait), end="")
        cpt_wait = cpt_wait + 1
        time.sleep(time_step)

    running = wsm.is_connected()

    if not running and (cpt_wait * time_step >= 30):
        print("Timeout...")

    result = None

    while running:
        a = input("Please write something\n")

        if a.lower() == "quit":
            running = False
        elif a.lower().startswith("help"):
            helper()
        elif a.lower().startswith("getresource"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            result = await wsm.send_and_wait(
                get_resouces(
                    args[1] if len(args) > 1 else "eml:///",
                    int(args[2]) if len(args) > 2 else 1,
                    args[3] if len(args) > 3 else None,
                )
            )
            if result:
                pretty_p.pprint(result)
                # pretty_p.pprint(result.body.__dict__)
                # get_res_resp
                pass
            else:
                print("No answer...")

        elif a.lower().startswith("putdataobject"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            for putDataObj in put_data_object_by_path(args[1], args[2] if len(args)>2 else None):
                result = await wsm.send_no_wait(putDataObj)
                if result:
                    pretty_p.pprint(result)
                    # pretty_p.pprint(result.body.__dict__)
                    # get_res_resp
                    pass
                else:
                    print("No answer...")

        elif a.lower().startswith("getdataarraymetadata"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            if len(args) <= 2 :
                print("Usage : GetDataArrayMetadata [URI] [PATH_IN_RESOURCES]")
            else:
                print(f"===> {args}\n")
                get_data_arr = get_data_array_metadata(args[1], args[2])
                print(f"\n\n{get_data_arr}\n\n")

                result = await wsm.send_no_wait(get_data_arr)
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

        elif a.lower().startswith("getdataarray") or a.lower().startswith("getdatasubarray"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            if len(args) <= 2 :
                print("Usage : GetDataSubArray [URI] [PATH_IN_RESOURCES] [START] [COUNT]")
            else:
                print(f"===> {args}\n")
                if len(args) > 4:  # subArray
                    get_data_arr = get_data_array(args[1], args[2], int(args[3]), int(args[4]))
                else:
                    get_data_arr = get_data_array(args[1], args[2])

                print(f"\n\n{get_data_arr}\n\n")
                result = await wsm.send_no_wait(get_data_arr)
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

        elif a.lower().startswith("getdataobject"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            get_data_obj = get_data_object(args[1:])
            # print("Sending : ", get_data_obj.__dict__)
            result = await wsm.send_and_wait(get_data_obj)
            if result:
                pretty_p.pprint(result)
                pass
            else:
                print("No answer...")

        elif a.lower().startswith("getdataspaces"):
            result = await wsm.send_and_wait(get_dataspaces())
            if result:
                pretty_p.pprint(result)
                pass
            else:
                print("No answer...")

        elif a.lower().startswith("putdataspace"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            try:
                result = await wsm.send_and_wait(put_dataspace(args[1:]))
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")
            except Exception as e:
                print(e)

        elif a.lower().startswith("putdataarray"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            try:
                if len(args)<3:
                    print("Not enough paratmeter : need a DATASPACE, an EPC_FILE_PATH and a H5_FILE_PATH")
                else:
                    uuid_list = args[1:-3] if len(args) > 4 else []
                    dataspace = args[-3]
                    epc_path = args[-2]
                    h5_path = args[-1]

                    async for msg_idx in put_data_array_sender(wsm, uuid_list, epc_path, h5_path, dataspace):
                        print(msg_idx)

                    # for pda in put_data_array(uuid_list, epc_path, h5_path, dataspace):
                    #     result = await wsm.send_no_wait(pda)
                    #     # result = await wsm.send_and_wait()
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
            except Exception as e:
                print(e)

        elif a.lower().startswith("deletedataspace"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            try:
                result = await wsm.send_and_wait(delete_dataspace(args[1:]))
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")
            except Exception as e:
                print(e)

        elif a.lower().startswith("closesession"):
            args = list(filter(lambda x: len(x) > 0, a.split(" ")))
            result = await wsm.send_and_wait(
                get_close_session(
                    args[1] if len(args) > 1 else "We have finished"
                )
            )
            await asyncio.sleep(1)
        else:
            print(a)

        if not wsm.is_connected():
            running = False

    end_message()

def main():

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None

    if (
        loop and loop.is_running()
    ):  # for case that an asyncio loop currently exists
        print(
            "Async event loop already running. Adding coroutine to the event loop."
        )
        tsk = loop.create_task(
            main(
                serv_url="localhost",
                serv_port=80,
                serv_sub_path="",
                serv_username="",
                serv_password="",
                serv_get_token_url="",
            )
        )
        # ^-- https://docs.python.org/3/library/asyncio-task.html#task-object
        # Optionally, a callback function can be executed when the coroutine completes
        # tsk.add_done_callback(
        #     lambda t: print(
        #         f"Task done with result={t.result()}  << return val of main()"
        #     )
        # )
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--host",
            # required=True,
            default="localhost",
            type=str,
            help="[Required] Server host (e.g. localhost or ip like XXX.XXX.XXX.XXX)",
        )
        parser.add_argument("--port", type=int, default=80, help="Server port")
        parser.add_argument(
            "--sub-path",
            type=str,
            help='Server sub-path (e.g. "etp" for an url like : "georisi.com/etp/")',
        )
        parser.add_argument(
            "--username", "-u", type=str, help="The user login"
        )
        parser.add_argument(
            "--password", "-p", type=str, help="The user password"
        )
        parser.add_argument(
            "--token-url", "-t", type=str, help="The server get token url"
        )
        args = parser.parse_args()

        asyncio.run(
            client(
                serv_url=args.host,
                serv_port=args.port,
                serv_sub_path=args.sub_path,
                serv_username=args.username,
                serv_password=args.password,
                serv_get_token_url=args.token_url,
            )
        )


if __name__ == "__main__":
    main()
