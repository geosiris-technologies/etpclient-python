#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import logging
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
    print(
        """[XXX] : replace XXX with your value
[XXX=Y] : replace XXX with your value, default is Y
[[XXX]] : optional parameter

[URI] for dataspaces can sometimes be set as "eml:///dataspace('DATASPACE_NAME')" but also with only the DATASPACE_NAME.

    Help : show this menu

    Quit : hard quit (no CloseSession sent)
    CloseSession : close this session

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

    Download              [OUTPU_FILE_PATH] [DATASPACE_NAME]

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
    if get_token_url:
        return requests.get(get_verified_url(get_token_url)).json()["token"]
    return None


def end_message(reason: str = None):
    print("1) Bye bye")


async def client(
    serv_url=None,
    serv_port=None,
    serv_sub_path=None,
    serv_username=None,
    serv_password=None,
    serv_get_token_url=None,
    serv_token=None,
    http_reqs=False,
):
    serv_uri = (
        str(serv_url)
        + (":" + str(serv_port) if serv_port else "")
        + ("/" + serv_sub_path + "/" if serv_sub_path else "")
    )

    if http_reqs:
        serv_uri_http = "http://" + serv_uri.split("://")[-1]

        print("Trying to contact server '" + str(serv_uri) + "'")
        print(
            "======> SERVER CAPS Test if contains :",
            ETPConnection.SUB_PROTOCOL,
        )
        try:
            server_caps_list_txt = requests.get(
                serv_uri_http
                + ".well-known/etp-server-capabilities?GetVersions=true"
            ).text
            pretty_p.pprint(server_caps_list_txt)
            # assert ETPConnection.SUB_PROTOCOL in json.loads(server_caps_list_txt)
        except:
            print("Failed to recover server caps version")

        print("======> SERVER CAPS :")
        try:
            server_caps_txt = requests.get(
                serv_uri_http
                + ".well-known/etp-server-capabilities?GetVersion="
                + ETPConnection.SUB_PROTOCOL
            ).text
            pretty_p.pprint(json.loads(server_caps_txt))
            print("<====== SERVER CAPS\n")
        except:
            print("Failed to recover server capabilities")

    serv_uri_ws = serv_uri
    if "://" not in serv_uri_ws:
        serv_uri_ws = "ws://" + serv_uri

    wsm = WebSocketManager(
        serv_uri_ws,
        username=serv_username,
        password=serv_password,
        token=get_token(serv_get_token_url) or serv_token,
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

    while running:
        a = input("Please write something\n")

        args = list(filter(lambda x: len(x) > 0, a.split(" ")))

        if len(args) > 0:
            command = args[0]
            command_params = args[1:]

            if a.lower() == "quit":
                running = False
            elif command.startswith("help"):
                helper()
            elif command.startswith("getresource"):
                result = await wsm.send_and_wait(
                    get_resouces(
                        command_params[0]
                        if len(command_params) > 0
                        else "eml:///",
                        int(command_params[1])
                        if len(command_params) > 1
                        else 1,
                        command_params[2] if len(command_params) > 2 else None,
                    )
                )
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

            elif command.startswith("putdataobject"):
                uuid_list = []
                print("args ", command_params, "\n>> ", a)
                if len(command_params) > 2:
                    uuid_list = command_params[2:]
                for putDataObj in put_data_object_by_path(
                    command_params[0],
                    command_params[1] if len(command_params) > 2 else None,
                    uuid_list,
                ):
                    result = await wsm.send_no_wait(putDataObj)
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")

            elif command.startswith("getdataarraymetadata"):
                if len(command_params) < 2:
                    print(
                        "Usage : GetDataArrayMetadata [URI] [PATH_IN_RESOURCES]"
                    )
                else:
                    print(f"===> {command_params}\n")
                    get_data_arr = get_data_array_metadata(
                        command_params[0], command_params[1]
                    )
                    print(f"\n\n{get_data_arr}\n\n")

                    result = await wsm.send_no_wait(get_data_arr)
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")

            elif command.startswith("getdataarray") or command.startswith(
                "getdatasubarray"
            ):
                if len(command_params) < 2:
                    print(
                        "Usage : GetDataSubArray [URI] [PATH_IN_RESOURCES] [START] [COUNT]"
                    )
                else:
                    print(f"===> {command_params}\n")
                    if len(command_params) > 3:  # subArray
                        get_data_arr = get_data_array(
                            command_params[0],
                            command_params[1],
                            int(command_params[2]),
                            int(command_params[3]),
                        )
                    else:
                        get_data_arr = get_data_array(
                            command_params[0], command_params[1]
                        )

                    print(f"\n\n{get_data_arr}\n\n")
                    result = await wsm.send_no_wait(get_data_arr)
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")

            elif command.startswith("getdataobject"):
                get_data_obj = get_data_object(command_params)
                result = await wsm.send_and_wait(get_data_obj)
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

            elif command.startswith("getdataspaces"):
                result = await wsm.send_and_wait(get_dataspaces())
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

            elif command.startswith("putdataspace"):
                try:
                    result = await wsm.send_and_wait(
                        put_dataspace(command_params)
                    )
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
                except Exception as e:
                    print(e)

            elif "supportedtypes" in command:
                try:
                    print("ARGS ", command_params)
                    result = await wsm.send_and_wait(
                        get_supported_types(
                            uri=command_params[0],
                            count=True
                            if len(command_params) < 2
                            else command_params[1],
                            return_empty_types=True
                            if len(command_params) < 3
                            else command_params[2],
                            scope="Self"
                            if len(command_params) < 4
                            else command_params[3],
                        )
                    )
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
                except Exception as e:
                    print(e)

            elif command.startswith("putdataarray"):
                try:
                    print(f"\n\nCommand is '{a}'")
                    if len(command_params) < 2:
                        print(
                            "Not enough paratmeter : need a DATASPACE, an EPC_FILE_PATH and a H5_FILE_PATH"
                        )
                    else:
                        type_filter = None
                        uuid_list = []
                        if command_params[0].lower().endswith("filter"):
                            type_filter = command_params[-1]
                        else:
                            print("UUID")
                            uuid_list = (
                                command_params[3:]
                                if len(command_params) > 3
                                else []
                            )
                        dataspace = command_params[0]
                        epc_path = command_params[1]
                        h5_path = command_params[2]
                        print(command_params)
                        print(
                            f"""uuid_list {uuid_list}
                            epc_path {epc_path}
                            h5_path {h5_path}
                            dataspace {dataspace}
                            type_filter {type_filter}"""
                        )

                        async for msg_idx in put_data_array_sender(
                            websocket=wsm,
                            uuids_filter=uuid_list,
                            epc_or_xml_file_path=epc_path,
                            h5_file_path=h5_path,
                            dataspace_name=dataspace,
                            type_filter=type_filter,
                        ):
                            print(msg_idx)

                        if result:
                            pretty_p.pprint(result)
                            pass
                        else:
                            print("No answer...")
                except Exception as e:
                    raise e

            elif command.startswith("deletedataobject"):
                try:
                    result = await wsm.send_and_wait(
                        delete_data_object(command_params)
                    )
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
                except Exception as e:
                    print(e)

            elif command.startswith("deletedataspace"):
                try:
                    result = await wsm.send_and_wait(
                        delete_dataspace(command_params)
                    )
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
                except Exception as e:
                    print(e)

            elif command.startswith("getdeletedresources"):
                try:
                    result = await wsm.send_and_wait(
                        get_deleted_resources(
                            dataspace_names=command_params[0],
                            delete_time_filter=command_params[1]
                            if len(command_params) > 1
                            else None,
                            data_object_types=command_params[2]
                            if len(command_params) > 2
                            else [],
                        )
                    )
                    if result:
                        pretty_p.pprint(result)
                        pass
                    else:
                        print("No answer...")
                except Exception as e:
                    print(e)

            elif command.startswith("closesession"):
                result = await wsm.send_and_wait(
                    get_close_session(
                        command_params[0]
                        if len(command_params) > 0
                        else "We have finished"
                    )
                )
                await asyncio.sleep(1)
            elif command == "download":
                await download_dataspace(
                    ws=wsm,
                    output_file_path=command_params[0],
                    dataspace_name=command_params[1]
                    if len(command_params) > 1
                    else None,
                )
            else:
                print(a)

        if not wsm.is_connected():
            running = False

    end_message()


def main():
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

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
        loop.create_task(
            main(
                serv_url="localhost",
                serv_port=80,
                serv_sub_path="",
                serv_username="",
                serv_password="",
                serv_get_token_url="",
                serv_token="",
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
        parser.add_argument(
            "--port", type=int, default=None, help="Server port"
        )
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
            "--token-url", type=str, help="The server get token url"
        )
        parser.add_argument("--token", "-t", type=str, help="An access token")
        parser.add_argument(
            "--caps", action="store_true", help="print http capabilities"
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
                serv_token=args.token,
                http_reqs=args.caps,
            )
        )


if __name__ == "__main__":
    main()
