#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import traceback
import asyncio
import logging
import pprint
import re
import sys
from io import StringIO
from pathlib import Path
from typing import TextIO
from urllib.parse import urlparse

from dotenv import load_dotenv
from etptypes.energistics.etp.v12.datatypes.any_array_type import AnyArrayType
from etptypes.energistics.etp.v12.datatypes.any_logical_array_type import AnyLogicalArrayType
from etptypes.energistics.etp.v12.datatypes.array_of_float import ArrayOfFloat
from etptypes.energistics.etp.v12.datatypes.data_array_types.data_array_metadata import DataArrayMetadata
from etptypes.energistics.etp.v12.datatypes.data_array_types.put_uninitialized_data_array_type import \
    PutUninitializedDataArrayType
from etptypes.energistics.etp.v12.protocol.data_array.put_uninitialized_data_arrays import PutUninitializedDataArrays
from etptypes.energistics.etp.v12.protocol.dataspace.get_dataspaces_response import GetDataspacesResponse

from etpclient.etp.requester import *
from etpclient.etp.runner import client, get_parser, get_parser_downloader
from etpclient.etp.serverprotocols import enable_logs
from etpclient.main import launch_command
from etpclient.rest_client import get_token_from_config
from etpclient.server_config import ServerConfig, SERVER_URL
from etpclient.websocket_manager import WebSocketManager

pretty_p = pprint.PrettyPrinter(width=80)  # , compact=True)


async def script_0(wsm: WebSocketManager):
    result = await wsm.send_and_wait(get_dataspaces())
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")
    return False


async def script_clean_fake_ds(wsm: WebSocketManager):
    result = await wsm.send_and_wait(get_dataspaces(), timeout=20)
    if result:
        pretty_p.pprint(result)
    else:
        print("No answer...")

    if isinstance(result, list):
        result = result[0]

    result = result.body

    if isinstance(result, GetDataspacesResponse):
        for d in result.dataspaces:
            uri = parse_uri(d.uri)
            if uri.dataspace.startswith("c-"):
                print(f"removing {uri.dataspace}")
                result = await wsm.send_and_wait(delete_dataspace([uri.dataspace]))
                if result:
                    pretty_p.pprint(result)
                    pass
                else:
                    print("No answer...")

    return False


async def download_objects(uris: List[str], wsm: WebSocketManager, output_folder: str = ""):
    try:
        os.makedirs(output_folder)
    except:
        pass
    for uri in uris:
        print(uri)
        f_path = Path(f"{output_folder}/{uri[7:]}.xml")
        if not os.path.exists(f_path):  # and "channel" not in uri.lower():
            data_obj = await wsm.send_and_wait(get_data_object(uris=[uri]), timeout=5)
            if data_obj is not None:
                try:
                    # p_uri = parse_uri(uri)
                    
                    if isinstance(data_obj[0].body, GetDataObjectsResponse):
                        with f_path.open("wb") as _f:
                            dos = data_obj[0].body.data_objects
                            _f.write(dos[list(dos.keys())[0]].data)
                    else:
                        print(f"\tNot readable : {data_obj[0].body}")
                except Exception as e:
                    print(f"\t Exception {e}\n\t{data_obj}")
                    print(traceback.format_exc())
            else:
                print(f"Failed to get Data object : {uri}")


def value_found_in_source(source: str, filterList: List[str]):
    for f in filterList:
        if f in source:
            return True
    return False


async def download_dataspace_objects(dataspace_uri: str, wsm: WebSocketManager, output_folder: str = "", filterQualifiedType: List[str]=[]):
    print(f"GetResources on {dataspace_uri}")
    logging.debug(f"filterQualifiedType : {filterQualifiedType}")
    dataspaces_objs = await wsm.send_and_wait(get_resouces(uri=dataspace_uri), timeout=60)
    uris = list(map(lambda r: r.uri, dataspaces_objs[0].body.resources))
    if(filterQualifiedType is not None and len(filterQualifiedType) > 0):
        uris = list(filter(lambda u: value_found_in_source(u, filterQualifiedType), uris))
    logging.debug(f"filtered : {uris}")
    if dataspaces_objs is not None:
        await download_objects(uris, wsm, output_folder)
    else:
        print(f"No data for {dataspace_uri}")


async def script_download_server(wsm: WebSocketManager, output_folder: str = "downloads", dataspaces: List[str] = [], filter: List[str]=[]):
    enable_logs(False)
    dataspaces_res = await wsm.send_and_wait(get_dataspaces(), timeout=10)

    dataspaces = ["eml:///"]
    try:
        if isinstance(dataspaces_res, list):
            dataspaces = dataspaces + list(map(lambda d: d.uri, dataspaces_res[0].body.dataspaces))
    except:
        pass
    for d_uri in dataspaces:
        p_uri = parse_uri(d_uri)
        print(d_uri, p_uri.dataspace)
        await download_dataspace_objects(d_uri, wsm, f"{output_folder}/{p_uri.dataspace}", filterQualifiedType=filter)
    # for m in dataspaces_res:
    #     if isinstance(m.body, GetDataspacesResponse):
    #         for d in m.body.dataspaces:
    #             p_uri = parse_uri(d.uri)
    #             print(d.uri, p_uri.dataspace)
    #             await download_dataspace_objects(d.uri, wsm, f"{output_folder}/{p_uri.dataspace}")
    return False


async def script_push_testing_package(
        wsm: WebSocketManager,
        dataspace_name="testing-package",
        epc_path="D:/Geosiris/Cloud/Resqml_Tools/2023-DATA/06_FESAPI_RESQML_WITSML_PRODML/testingPackageCpp.epc",
        h5_path="D:/Geosiris/Cloud/Resqml_Tools/2023-DATA/06_FESAPI_RESQML_WITSML_PRODML/testingPackageCpp.h5",
):
    print(f"PutDataSpace {dataspace_name}")
    result = await wsm.send_and_wait(
        put_dataspace([dataspace_name])
    )
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    for putDataObj in put_data_object_by_path(
            path=epc_path,
            dataspace_name=dataspace_name,
            uuids_filter=[],
    ):
        result = await wsm.send_no_wait(putDataObj)
        if result:
            pretty_p.pprint(result)
            pass
        else:
            print("No answer...")

    async for msg_idx in put_data_array_sender(
            websocket=wsm,
            uuids_filter=[],
            epc_or_xml_file_path=epc_path,
            h5_file_path=h5_path,
            dataspace_name=dataspace_name,
            type_filter=None,
    ):
        print(msg_idx)

    return False


async def script_put_sub_array(wsm: WebSocketManager):
    # uri = "eml:///resqml22.FakeData(956103f2-1c9f-418e-a9ee-679a26be697b)"
    uri = "eml:///dataspace('volve-eqn-plus')/resqml22.TriangulatedSetRepresentation(f3a44228-4f8e-47a7-b999-86f50c3b5857)"
    path_in_resource = "RESQML/f3a44228-4f8e-47a7-b999-86f50c3b5857/fake_2"

    # full_data = [
    #     "01", "02", "03", "04", "05", "06", "07", "08", "09",
    #     "11", "12", "13", "14", "15", "16", "17", "18", "19",
    #     "21", "22", "23", "24", "25", "26", "27", "28", "29"
    # ]
    full_data = [float(i) for i in range(27)]
    dims = [3, 3, 3]

    # TODO: run a putSubArrayRequest
    # PutUninitializedDataArrays
    # PutDataSubarrays
    print("Sending PutUninitializedDataArrays")
    result = await wsm.send_and_wait(PutUninitializedDataArrays(
        data_arrays={
            "0": PutUninitializedDataArrayType(
                uid=DataArrayIdentifier(
                    uri=uri,
                    path_in_resource=path_in_resource,
                ),
                metadata=DataArrayMetadata(
                    dimensions=dims,
                    transport_array_type=AnyArrayType.ARRAY_OF_FLOAT,
                    # transport_array_type=AnyArrayType.ARRAY_OF_STRING,
                    logical_array_type=AnyLogicalArrayType.ARRAY_OF_FLOAT32_LE,
                    # logical_array_type=AnyLogicalArrayType.ARRAY_OF_STRING,
                    store_last_write=0,
                    store_created=0,
                    preferred_subarray_dimensions=[],
                    custom_data=[],
                )
            )
        }
    ))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending get_data_array")
    result = await wsm.send_and_wait(get_data_array(uri=uri, path_in_res=path_in_resource))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending PutDataSubarrays (1/3)")
    result = await wsm.send_and_wait(PutDataSubarrays(
        data_subarrays={
            "0": PutDataSubarraysType(
                uid=DataArrayIdentifier(
                    uri=uri,
                    path_in_resource=path_in_resource,
                ),
                data=AnyArray(item=ArrayOfFloat(values=full_data[0:9])),
                # data=AnyArray(item=ArrayOfString(values=full_data[0:8])),
                starts=[0, 0, 0],
                counts=[1, 3, 3],
            )
        }
    ))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending get_data_array")
    result = await wsm.send_and_wait(get_data_array(uri=uri, path_in_res=path_in_resource))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending PutDataSubarrays (2/3)")
    result = await wsm.send_and_wait(PutDataSubarrays(
        data_subarrays={
            "0": PutDataSubarraysType(
                uid=DataArrayIdentifier(
                    uri=uri,
                    path_in_resource=path_in_resource,
                ),
                data=AnyArray(item=ArrayOfFloat(values=full_data[9:18])),
                # data=AnyArray(item=ArrayOfString(values=full_data[0:8])),
                starts=[1, 0, 0],
                counts=[1, 3, 3],
            )
        }
    ))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending get_data_array")
    result = await wsm.send_and_wait(get_data_array(uri=uri, path_in_res=path_in_resource))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending PutDataSubarrays (3/3)")
    result = await wsm.send_and_wait(PutDataSubarrays(
        data_subarrays={
            "0": PutDataSubarraysType(
                uid=DataArrayIdentifier(
                    uri=uri,
                    path_in_resource=path_in_resource,
                ),
                data=AnyArray(item=ArrayOfFloat(values=full_data[18:27])),
                # data=AnyArray(item=ArrayOfString(values=full_data[0:8])),
                starts=[2, 0, 0],
                counts=[1, 3, 3],
            )
        }
    ))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    print("Sending get_data_array")
    result = await wsm.send_and_wait(get_data_array(uri=uri, path_in_res=path_in_resource))
    if result:
        pretty_p.pprint(result)
        pass
    else:
        print("No answer...")

    return False


# Main functions :


def test_put_sub_array():
    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    args = get_parser().parse_args()

    asyncio.run(
        client(
            run_func=script_put_sub_array,
            config=config,
            server_capabilities=args.caps,
        )
    )


def download_xmls():
    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    args = get_parser_downloader().parse_args()

    host_name = urlparse(config.get(SERVER_URL)).hostname
    print(args.filter)

    asyncio.run(
        client(
            run_func=lambda wsm: script_download_server(wsm, output_folder=f"downloads/{host_name}", filter=args.filter),
            config=config,
            server_capabilities=args.caps,
        )
    )


async def script_upload(
        wsm: WebSocketManager,
        dataspace_name: str = None,
        uuid_filter: List = None,
        epc_path: str = None,
        h5_paths: List = None,
):
    if uuid_filter is None:
        uuid_filter = []
    if h5_paths is None:
        h5_paths = []

    for putDataObj in put_data_object_by_path(
            path=epc_path,
            dataspace_name=dataspace_name,
            uuids_filter=uuid_filter,
    ):
        result = await wsm.send_no_wait(putDataObj)
        if result:
            pretty_p.pprint(result)
            pass
        else:
            print("No answer...")

    for h5_path in h5_paths:
        async for msg_idx in put_data_array_sender(
                websocket=wsm,
                uuids_filter=uuid_filter,
                epc_or_xml_file_path=epc_path,
                h5_file_path=h5_path,
                dataspace_name=dataspace_name,
                type_filter=None,
        ):
            print(msg_idx)

    return False


def upload():
    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    args, unknown_args = get_parser().parse_known_args()

    host_name = urlparse(config.get(SERVER_URL)).hostname

    print(unknown_args)
    if len(unknown_args) < 2:
        print("Usage : poetry run upload [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH]* [UUID_FILTER]*\n"
              "If no uuid provided, all elements will be pushed")
        return

    dataspace = unknown_args[0]
    epc_path = None
    h5_paths = []
    uuid_filter = []

    for ua in unknown_args:
        if ua.lower().endswith(".epc") and epc_path is None:
            epc_path = ua
        elif ua.lower().endswith(".h5"):
            h5_paths.append(ua)
        elif re.match(UUID_REGEX, ua):
            uuid_filter.append(ua)

    asyncio.run(
        client(
            run_func=lambda wsm: script_upload(
                wsm,
                dataspace_name=dataspace,
                uuid_filter=uuid_filter,
                epc_path=epc_path,
                h5_paths=h5_paths
            ),
            config=config,
            server_capabilities=args.caps,
        )
    )


def init_gabbro():
    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    args = get_parser().parse_args()

    host_name = urlparse(args.host).hostname

    asyncio.run(
        client(
            run_func=script_push_testing_package,
            config=config,
            server_capabilities=args.caps,
        )
    )


async def _file_script_line_reader(wsm: WebSocketManager, fio: TextIO):
    line = fio.readline()

    if line is not None:
        line = line.strip()
        while len(line) > 0 and not line.startswith("#"):
            return await launch_command(wsm=wsm, cmd=line)

    if (line is None or len(line) > 0) and wsm.is_connected():
        print("quitting")
        return await launch_command(wsm=wsm, cmd="quit")
    return True


def file_script(f_path: Optional[str] = None):
    if f_path is None:
        f_path = sys.argv[1]

    print(f"reading {f_path}")

    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    with open(f_path, "r") as f:
        async def _consumer(wsm):
            return await _file_script_line_reader(wsm=wsm, fio=f)

        asyncio.run(
            client(
                run_func=_consumer,
                config=config,
                server_capabilities=False,
            )
        )


def main():
    load_dotenv(override=True)
    config = ServerConfig()
    logging.basicConfig(filename="etpclient.log", level=logging.DEBUG)

    args = get_parser().parse_args()

    host_name = urlparse(args.host).hostname

    asyncio.run(
        client(
            # run_func=script_0,
            run_func=script_clean_fake_ds,
            config=config,
            server_capabilities=args.caps,
        )
    )


if __name__ == "__main__":
    f_name = sys.argv.pop(1)
    print(sys.argv)
    print(f_name)
    load_dotenv(override=True)
    config = ServerConfig()
    # print(get_token_from_config(config))
    globals()[f_name]()
