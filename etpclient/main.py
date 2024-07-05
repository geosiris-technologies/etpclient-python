#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import asyncio
import logging
import pprint

from dotenv import load_dotenv

from etpclient.etp.requester import *
from etpclient.etp.runner import client, get_parser
from etpclient.server_config import ServerConfig
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
    DownloadObject        [OUTPUT_FOLDER_PATH] [URI]

    GetSupportedTypes     [URI] [[COUNT=True]] [[RETURN_EMPTY_TYPES=True]] [[SCOPE=Self]]
"""
    )


async def launch_command(wsm: WebSocketManager, cmd: str) -> bool:
    args = list(filter(lambda x: len(x) > 0, cmd.split(" ")))
    command = args[0].lower()
    command_params = args[1:] if len(args) > 1 else []

    if command == "quit":
        return False
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
                command_params[3:] if len(command_params) > 3 else [],
            )
        )
        if result:
            pretty_p.pprint(result)
            pass
        else:
            print("No answer...")

    elif command.startswith("requestsession"):
        result = await wsm.send_and_wait(request_session())
        if result:
            pretty_p.pprint(result)
            pass
        else:
            print("No answer...")

    elif command.startswith("authorize"):
        authorize_msg = None
        if len(command_params) == 1:
            authorize_msg = authorize_bearer(command_params[0])
        elif len(command_params) == 2:
            print("Basic auth")
            authorize_msg = authorize_basic(command_params[0], command_params[1])

        if authorize_msg is not None:
            result = await wsm.send_and_wait(authorize_msg)
            if result:
                pretty_p.pprint(result)
                pass
            else:
                print("No answer...")
    elif command.startswith("putdataobject"):
        uuid_list = []
        print("args ", command_params, "\n>> ", cmd)
        if len(command_params) > 2:
            uuid_list = command_params[2:]
        for putDataObj in put_data_object_by_path(
                path=command_params[0],
                dataspace_name=command_params[1] if len(command_params) > 1 else None,
                uuids_filter=uuid_list,
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

    elif command.startswith("getdataspace"):
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
            print(f"\n\nCommand is '{cmd}'")
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
        await wsm.send_and_wait(
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
    elif command == "downloadobject":
        await download_xml_and_h5(
            ws=wsm,
            output_folder=command_params[0],
            uri=command_params[1]
        )
    elif command == "msg":
        await wsm.send_raw(" ".join(command_params).encode("utf-8"))
    else:
        print(command)

    return True


async def client_ui(wsm: WebSocketManager) -> bool:
    a = input("Please write something\n")

    return await launch_command(wsm=wsm, cmd=a)


def main():
    load_dotenv(override=True)
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)
    config = ServerConfig()
    print(f"config {config}")
    print(f"INI_FILE_PATH {os.environ['INI_FILE_PATH']}")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None

    args = get_parser().parse_args()

    if (
            loop and loop.is_running()
    ):  # for case that an asyncio loop currently exists
        print(
            "Async event loop already running. Adding coroutine to the event loop."
        )
        loop.create_task(
            client(
                run_func=client_ui,
                config=config,
                server_capabilities=args.caps,
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

        asyncio.run(
            client(
                run_func=client_ui,
                config=config,
                # serv_url=args.host,
                # serv_port=args.port,
                # serv_sub_path=args.sub_path,
                # serv_username=args.username,
                # serv_password=args.password,
                # serv_get_token_url=args.token_url,
                # serv_token=args.token,
                server_capabilities=args.caps,
            )
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    load_dotenv(override=True)
    main()
    # print(ServerConfig().get_config())
