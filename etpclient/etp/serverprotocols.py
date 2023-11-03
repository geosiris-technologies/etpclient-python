#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
from typing import Union, AsyncGenerator, Optional
from datetime import datetime
import uuid as pyUUID
import pprint
import lxml.etree as etree
import json

from etpproto.messages import Message
from etptypes.energistics.etp.v12.datatypes.message_header import MessageHeader

from etptypes import avro_schema

from etpproto.connection import CommunicationProtocol, Protocol, ETPConnection
from etpproto.client_info import ClientInfo

from etpproto.protocols.core import CoreHandler
from etpproto.protocols.discovery import DiscoveryHandler
from etpproto.protocols.store import StoreHandler
from etpproto.protocols.data_array import DataArrayHandler
from etpproto.protocols.supported_types import SupportedTypesHandler
from etpproto.protocols.dataspace import DataspaceHandler

from etptypes.energistics.etp.v12.datatypes.data_value import DataValue
from etptypes.energistics.etp.v12.datatypes.contact import Contact
from etptypes.energistics.etp.v12.datatypes.object.data_object import (
    DataObject,
)
from etptypes.energistics.etp.v12.datatypes.object.dataspace import Dataspace
from etptypes.energistics.etp.v12.datatypes.object.deleted_resource import (
    DeletedResource,
)
from etptypes.energistics.etp.v12.datatypes.object.put_response import (
    PutResponse,
)
from etptypes.energistics.etp.v12.datatypes.object.resource import Resource
from etptypes.energistics.etp.v12.datatypes.object.supported_type import (
    SupportedType,
)
from etptypes.energistics.etp.v12.datatypes.server_capabilities import (
    ServerCapabilities,
)
from etptypes.energistics.etp.v12.datatypes.supported_data_object import (
    SupportedDataObject,
)
from etptypes.energistics.etp.v12.datatypes.supported_protocol import (
    SupportedProtocol,
)
from etptypes.energistics.etp.v12.datatypes.uuid import Uuid
from etptypes.energistics.etp.v12.datatypes.version import *
from etptypes.energistics.etp.v12.protocol.core.close_session import (
    CloseSession,
)
from etptypes.energistics.etp.v12.protocol.core.open_session import OpenSession
from etptypes.energistics.etp.v12.protocol.core.ping import Ping
from etptypes.energistics.etp.v12.protocol.core.pong import Pong
from etptypes.energistics.etp.v12.protocol.core.protocol_exception import (
    ProtocolException,
)
from etptypes.energistics.etp.v12.protocol.core.request_session import (
    RequestSession,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_array_metadata import (
    GetDataArrayMetadata,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_array_metadata_response import (
    GetDataArrayMetadataResponse,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_arrays import (
    GetDataArrays,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_arrays_response import (
    GetDataArraysResponse,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_subarrays import (
    GetDataSubarrays,
)
from etptypes.energistics.etp.v12.protocol.data_array.get_data_subarrays_response import (
    GetDataSubarraysResponse,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_data_arrays import (
    PutDataArrays,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_data_arrays_response import (
    PutDataArraysResponse,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_data_subarrays import (
    PutDataSubarrays,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_data_subarrays_response import (
    PutDataSubarraysResponse,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_uninitialized_data_arrays import (
    PutUninitializedDataArrays,
)
from etptypes.energistics.etp.v12.protocol.data_array.put_uninitialized_data_arrays_response import (
    PutUninitializedDataArraysResponse,
)
from etptypes.energistics.etp.v12.protocol.dataspace.delete_dataspaces import (
    DeleteDataspaces,
)
from etptypes.energistics.etp.v12.protocol.dataspace.delete_dataspaces_response import (
    DeleteDataspacesResponse,
)
from etptypes.energistics.etp.v12.protocol.dataspace.get_dataspaces import (
    GetDataspaces,
)
from etptypes.energistics.etp.v12.protocol.dataspace.get_dataspaces_response import (
    GetDataspacesResponse,
)
from etptypes.energistics.etp.v12.protocol.dataspace.put_dataspaces import (
    PutDataspaces,
)
from etptypes.energistics.etp.v12.protocol.dataspace.put_dataspaces_response import (
    PutDataspacesResponse,
)
from etptypes.energistics.etp.v12.protocol.discovery.get_deleted_resources import (
    GetDeletedResources,
)
from etptypes.energistics.etp.v12.protocol.discovery.get_deleted_resources_response import (
    GetDeletedResourcesResponse,
)
from etptypes.energistics.etp.v12.protocol.discovery.get_resources import (
    GetResources,
)
from etptypes.energistics.etp.v12.protocol.discovery.get_resources_response import (
    GetResourcesResponse,
)
from etptypes.energistics.etp.v12.protocol.store.delete_data_objects import (
    DeleteDataObjects,
)
from etptypes.energistics.etp.v12.protocol.store.get_data_objects import (
    GetDataObjects,
)
from etptypes.energistics.etp.v12.protocol.store.get_data_objects_response import (
    GetDataObjectsResponse,
)
from etptypes.energistics.etp.v12.protocol.store.put_data_objects import (
    PutDataObjects,
)
from etptypes.energistics.etp.v12.protocol.store.put_data_objects_response import (
    PutDataObjectsResponse,
)
from etptypes.energistics.etp.v12.protocol.store.delete_data_objects_response import (
    DeleteDataObjectsResponse,
)
from etptypes.energistics.etp.v12.protocol.supported_types.get_supported_types import (
    GetSupportedTypes,
)

from etptypes.energistics.etp.v12.protocol.supported_types.get_supported_types_response import (
    GetSupportedTypesResponse,
)


# from geoetp.etp.etp_data_bridge import ETPDataBridge
# from geoetp.etp.hsds_bridge import HSDSBridge


pretty_p = pprint.PrettyPrinter(width=100, compact=True)

# etp_bridge = ETPDataBridge()

#    ______                                    __                   __
#   / ____/___  ________     ____  _________  / /_____  _________  / /
#  / /   / __ \/ ___/ _ \   / __ \/ ___/ __ \/ __/ __ \/ ___/ __ \/ /
# / /___/ /_/ / /  /  __/  / /_/ / /  / /_/ / /_/ /_/ / /__/ /_/ / /
# \____/\____/_/   \___/  / .___/_/   \____/\__/\____/\___/\____/_/
#                        /_/


def print_resource(res: Resource):
    print("Resource :", res.uri)
    print("\tSource count :", res.source_count)
    print("\tTarget count :", res.target_count)
    # print("\tLast change :", datetime.fromtimestamp(res.last_changed))


def print_dataspace(res: Dataspace):
    print("Dataspace :", res.uri)
    print("\tStore last write :", res.store_last_write)
    print("\tStore created :", res.store_created)
    print("\tPath :", res.path)
    print("\ttCustom data :", res.custom_data)
    # print("\tLast change :", datetime.fromtimestamp(res.last_changed))


def print_protocol_exception(pe: ProtocolException):
    if pe.error is not None:
        print("Error recieved : " + str(pe))
    elif len(pe.errors) > 0:
        print(f"Errors recieved ({pe.errors}): ")
        for code, pe in pe.errors.items():
            print(f"\t{code}) {str(pe)}")


@ETPConnection.on(CommunicationProtocol.CORE)
class myCoreProtocol(CoreHandler):

    uuid: Uuid = pyUUID.uuid4()

    async def on_open_session(
        self,
        msg: OpenSession,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print("OpenSession recieved")
        yield

    async def on_close_session(
        self,
        msg: CloseSession,
        correlation_id: int,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_close_session")
        yield

    async def on_ping(
        self,
        msg: Ping,
        correlation_id: int,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": #Core : Ping recieved")
        yield Message.get_object_message(
            Pong(currentDateTime=int(datetime.utcnow().timestamp())),
            correlation_id=correlation_id,
        )

    async def on_pong(
        self,
        msg: Pong,
        correlation_id: int,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": #Core : Pong recieved")
        yield

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print_protocol_exception(msg)
        yield


#     ____  _                                         ____             __                   __
#    / __ \(_)_____________ _   _____  _______  __   / __ \_________  / /_____  _________  / /
#   / / / / / ___/ ___/ __ \ | / / _ \/ ___/ / / /  / /_/ / ___/ __ \/ __/ __ \/ ___/ __ \/ /
#  / /_/ / (__  ) /__/ /_/ / |/ /  __/ /  / /_/ /  / ____/ /  / /_/ / /_/ /_/ / /__/ /_/ / /
# /_____/_/____/\___/\____/|___/\___/_/   \__, /  /_/   /_/   \____/\__/\____/\___/\____/_/
#                                        /____/


@ETPConnection.on(CommunicationProtocol.DISCOVERY)
class myDiscoveryProtocol(DiscoveryHandler):
    async def on_get_resources_response(
        self,
        msg: GetResourcesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(
            "## myDiscoveryProtocol ## on_get_resources_response : nb[",
            len(msg.resources),
            "]",
        )
        for res in msg.resources:
            print_resource(res)
        yield

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print_protocol_exception(msg)
        yield

    async def on_get_deleted_resources_response(
        self,
        msg: GetDeletedResourcesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        if msg is not None:
            if len(msg.deleted_resources) > 0:
                print(f"Deleted object list ({len(msg.deleted_resources)}) : ")
                for dr in msg.deleted_resources:
                    print(f"\t{dr.uri} \tdeleted_time: \t{dr.deleted_time}")
            else:
                print("No deleted resource found for this context")

        yield


#     ____        __
#    / __ \____ _/ /_____ __________  ____ _________  _____
#   / / / / __ `/ __/ __ `/ ___/ __ \/ __ `/ ___/ _ \/ ___/
#  / /_/ / /_/ / /_/ /_/ (__  ) /_/ / /_/ / /__/  __(__  )
# /_____/\__,_/\__/\__,_/____/ .___/\__,_/\___/\___/____/
#                           /_/


@ETPConnection.on(CommunicationProtocol.DATASPACE)
class myDataspaceHandler(DataspaceHandler):
    async def on_delete_dataspaces(
        self,
        msg: DeleteDataspaces,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_delete_dataspaces")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_get_dataspaces(
        self,
        msg: GetDataspaces,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_dataspaces")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_put_dataspaces(
        self,
        msg: PutDataspaces,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_put_dataspaces")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_delete_dataspaces_response(
        self,
        msg: DeleteDataspacesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        pretty_p.pprint(msg)
        yield
        # raise NotSupportedError()

    async def on_get_dataspaces_response(
        self,
        msg: GetDataspacesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        for dataspace in msg.dataspaces:
            print_dataspace(dataspace)
        yield
        # raise NotSupportedError()

    async def on_put_dataspaces_response(
        self,
        msg: PutDataspacesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        pretty_p.pprint(msg)
        yield
        # raise NotSupportedError()

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print_protocol_exception(msg)

        yield


#    _____ __                     ____             __                   __
#   / ___// /_____  ________     / __ \_________  / /_____  _________  / /
#   \__ \/ __/ __ \/ ___/ _ \   / /_/ / ___/ __ \/ __/ __ \/ ___/ __ \/ /
#  ___/ / /_/ /_/ / /  /  __/  / ____/ /  / /_/ / /_/ /_/ / /__/ /_/ / /
# /____/\__/\____/_/   \___/  /_/   /_/   \____/\__/\____/\___/\____/_/


@ETPConnection.on(CommunicationProtocol.STORE)
class myStoreProtocol(StoreHandler):
    async def on_get_data_objects(
        self,
        msg: GetDataObjects,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_data_objects")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_put_data_objects(
        self,
        msg: PutDataObjects,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_put_data_objects")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_delete_data_objects(
        self,
        msg: DeleteDataObjects,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_delete_data_objects")
        etpObj, etpErr = await etp_bridge.handle_request(msg, client_info)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_get_data_objects_response(
        self,
        msg: GetDataObjectsResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print("# on_get_data_objects_response")
        # pretty_p.pprint(msg)
        for do in msg.data_objects.values():
            form = do.format_.lower()
            try:
                if form == "xml":
                    print(do.data.decode("utf-8"))
                elif form == "json":
                    json.dumps(
                        json.loads(do.data.data.decode("utf-8")), indent=4
                    )
            except Exception as e:
                print("\n\n=============", e, "\n")
                pretty_p.pprint(do)

        yield

    async def on_put_data_objects_response(
        self,
        msg: PutDataObjectsResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(f"Success {len(msg.success)}:")
        for code, pr in msg.success.items():
            print(f"\t{code}) {str(pr.created_contained_object_uris)}")
        yield

    async def on_delete_data_objects_response(
        self,
        msg: DeleteDataObjectsResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print(f"Deletion success {len(msg.deleted_uris)}:")
        for code, aos in msg.deleted_uris.items():
            print(f"\t{code}) {str(aos)}")
        yield

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print_protocol_exception(msg)
        yield


#     ____        __        ___                             ____             __                   __
#    / __ \____ _/ /_____ _/   |  ______________ ___  __   / __ \_________  / /_____  _________  / /
#   / / / / __ `/ __/ __ `/ /| | / ___/ ___/ __ `/ / / /  / /_/ / ___/ __ \/ __/ __ \/ ___/ __ \/ /
#  / /_/ / /_/ / /_/ /_/ / ___ |/ /  / /  / /_/ / /_/ /  / ____/ /  / /_/ / /_/ /_/ / /__/ /_/ / /
# /_____/\__,_/\__/\__,_/_/  |_/_/  /_/   \__,_/\__, /  /_/   /_/   \____/\__/\____/\___/\____/_/
#                                              /____/


@ETPConnection.on(CommunicationProtocol.DATA_ARRAY)
class myDataArrayHandler(DataArrayHandler):
    # hsdsbridge: HSDSBridge = HSDSBridge('alwyn')

    async def on_get_data_array_metadata(
        self,
        msg: GetDataArrayMetadata,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_data_array_metadata")
        etpObj, etpErr = myDataArrayHandler.hsdsbridge.handle_metadata(msg)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_get_data_array_metadata_response(
        self,
        msg: GetDataArrayMetadataResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print(client_info.ip, msg)
        yield

    async def on_get_data_arrays(
        self,
        msg: GetDataArrays,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_data_arrays")
        etpObj, etpErr = myDataArrayHandler.hsdsbridge.send_request(msg)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_get_data_subarrays(
        self,
        msg: GetDataSubarrays,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_data_subarrays")
        etpObj, etpErr = myDataArrayHandler.hsdsbridge.send_request(msg)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_get_data_arrays_response(
        self,
        msg: GetDataArraysResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print(client_info.ip, msg)
        yield

    async def on_get_data_subarrays_response(
        self,
        msg: GetDataSubarraysResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print(client_info.ip, msg)
        yield

    async def on_put_data_arrays(
        self,
        msg: PutDataArrays,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_put_data_arrays")
        etpObj, etpErr = myDataArrayHandler.hsdsbridge.send_request(msg)
        yield Message.get_object_message(etpObj, correlation_id=correlation_id)
        yield etpErr

    async def on_put_data_arrays_response(
        self,
        msg: PutDataArraysResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print(client_info.ip, msg)
        yield

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[Optional[Message], None]:
        print_protocol_exception(msg)
        yield


#    _____                              __           ________
#   / ___/__  ______  ____  ____  _____/ /____  ____/ /_  __/_  ______  ___  _____
#   \__ \/ / / / __ \/ __ \/ __ \/ ___/ __/ _ \/ __  / / / / / / / __ \/ _ \/ ___/
#  ___/ / /_/ / /_/ / /_/ / /_/ / /  / /_/  __/ /_/ / / / / /_/ / /_/ /  __(__  )
# /____/\__,_/ .___/ .___/\____/_/   \__/\___/\__,_/ /_/  \__, / .___/\___/____/
#           /_/   /_/                                    /____/_/


@ETPConnection.on(CommunicationProtocol.SUPPORTED_TYPES)
class mySupportedTypesProtocol(SupportedTypesHandler):
    async def on_get_supported_types(
        self,
        msg: GetSupportedTypes,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print(client_info.ip, ": on_get_supported_types")
        yield

    async def on_get_supported_types_response(
        self,
        msg: GetSupportedTypesResponse,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        for st in msg.supported_types:
            print(f"\t{st.data_object_type}\t count : {str(st.object_count)}")
        yield

    async def on_protocol_exception(
        self,
        msg: ProtocolException,
        msg_header: MessageHeader,
        client_info: Union[None, ClientInfo] = None,
    ) -> AsyncGenerator[bytes, None]:
        print_protocol_exception(msg)
        yield


#    _____                              ______
#   / ___/___  ______   _____  _____   / ____/___ _____  _____
#   \__ \/ _ \/ ___/ | / / _ \/ ___/  / /   / __ `/ __ \/ ___/
#  ___/ /  __/ /   | |/ /  __/ /     / /___/ /_/ / /_/ (__  )
# /____/\___/_/    |___/\___/_/      \____/\__,_/ .___/____/
#                                              /_/

# ATTENTION : A FAIRE EN DERNIER ! a cause de supportedProtocolList_fun()
@ETPConnection.dec_server_capabilities()
def computeCapability(supportedProtocolList_fun) -> ServerCapabilities:
    protocolDict = supportedProtocolList_fun()

    # pretty_p.pprint(protocolDict)

    return ServerCapabilities(
        application_name="etpproto",
        application_version="1.1.2",
        supported_protocols=list(
            map(
                lambda d: SupportedProtocol(
                    protocol=d.protocol,
                    protocol_version=d.protocol_version,
                    role="store",
                    protocol_capabilities=d.protocol_capabilities,
                ),
                protocolDict,
            )
        ),
        supported_data_objects=[
            # SupportedDataObject(
            #     qualified_type="resqml20.*",
            #     data_object_capabilities={}),
            # data_object_capabilities={"SupportsGet": True, "SupportsPut": True, "SupportsDelete": True}),
            # SupportedDataObject(
            #     qualified_type="resqml22.*",
            #     data_object_capabilities={}),
            #     # data_object_capabilities={"SupportsGet": True, "SupportsPut": True, "SupportsDelete": True})
            # SupportedDataObject({'dataObjectCapabilities': {'SupportsDelete': {'item': {'boolean': True}},
            #                                           'SupportsGet': {'item': {'boolean': True}},
            #                                           'SupportsPut': {'item': {'boolean': True}}
            #                                           )
            SupportedDataObject(
                qualified_type="eml20.*",
                data_object_capabilities={
                    "SupportsDelete": DataValue(item=True),
                    "SupportsPut": DataValue(item=True),
                    "SupportsGet": DataValue(item=True),
                },
            ),
            SupportedDataObject(
                qualified_type="resqml20.*",
                data_object_capabilities={
                    "SupportsDelete": DataValue(item=True),
                    "SupportsPut": DataValue(item=True),
                    "SupportsGet": DataValue(item=True),
                },
            ),
        ],
        # supported_compression=["gzip"],
        supported_formats=["xml"],
        endpoint_capabilities={
            "MaxWebSocketMessagePayloadSize": DataValue(item=4000)
        },
        supported_encodings=["binary"],
        contact_information=Contact(
            organization_name="Geosiris",
            contact_name="Gauthier Valentin, Untereiner Lionel",
            contact_phone="",
            contact_email="valentin.gauthier@geosiris.com, lionel.untereiner@geosiris.com",
        ),
    )
