import httpx
import json
import datetime

import uuid as pyUUID

import typing
from base64 import b64encode

from etptypes.energistics.etp.v12.protocol.discovery import (
    GetResources,
    GetResourcesResponse,
    GetDeletedResources,
    GetDeletedResourcesResponse,
)
from etptypes.energistics.etp.v12.protocol.store import (
    PutDataObjects,
    PutDataObjectsResponse,
    GetDataObjects,
    GetDataObjectsResponse,
    DeleteDataObjects,
    DeleteDataObjectsResponse,
)

from etptypes.energistics.etp.v12.protocol.dataspace import (
    DeleteDataspaces,
    DeleteDataspacesResponse,
    GetDataspaces,
    GetDataspacesResponse,
    PutDataspaces,
    PutDataspacesResponse,
)

from etptypes.energistics.etp.v12.protocol.supported_types import (
    GetSupportedTypes,
    GetSupportedTypesResponse,
)

from etptypes.energistics.etp.v12.datatypes.object import (
    Resource,
    DataObject,
    PutResponse,
    DeletedResource,
    SupportedType,
    Dataspace,
)

from etptypes.energistics.etp.v12.datatypes import ArrayOfString

from etptypes.energistics.etp.v12.datatypes.uuid import to_Uuid

from etpproto.uri import *
from etpproto.error import (
    ETPError,
    RequestDeniedError,
    NotFoundError,
)
from etpproto.client_info import ClientInfo


class ETPDataBridge:
    requestPage: str = "request"
    requestObjects: str = "request"

    def __init__(self):
        pass
        # self.host = host
        # self.port = port
        # if("http://" in self.host):
        #     self.url = self.host + ":" + self.port
        # else:
        #     self.url = "http://" + self.host + ":" + self.port

    async def handle_request(
        self, etp_req, client_info: typing.Union[None, ClientInfo] = None
    ):
        # print("Sending request to ingester at url : '", self.url, "'")
        try:
            if isinstance(etp_req, GetResources):
                return await self.handle_get_resources(client_info, etp_req)
            elif isinstance(etp_req, GetDataObjects):
                return await self.handle_get_data_objects(client_info, etp_req)
            elif isinstance(etp_req, PutDataObjects):
                return await self.handle_put_data_objects(client_info, etp_req)
            elif isinstance(etp_req, DeleteDataObjects):
                return await self.handle_delete_data_objects(
                    client_info, etp_req
                )
            elif isinstance(etp_req, GetDeletedResources):
                return await self.handle_get_deleted_resources(
                    client_info, etp_req
                )
            elif isinstance(etp_req, GetSupportedTypes):
                return await self.handle_get_supported_types(
                    client_info, etp_req
                )
            elif isinstance(etp_req, DeleteDataspaces):
                return await self.handle_delete_dataspaces(
                    client_info, etp_req
                )
            elif isinstance(etp_req, GetDataspaces):
                return await self.handle_get_dataspaces(client_info, etp_req)
            elif isinstance(etp_req, PutDataspaces):
                return await self.handle_put_dataspaces(client_info, etp_req)
            else:
                print(
                    "#ETPDataBridge can not handle request of type ",
                    type(etp_req),
                )
                return None, None
        except httpx.RequestError as e:  # This is the correct syntax
            print("\n#RDMS : error in connection\n")
            return None, RequestDeniedError(
                "Geosiris RDMS has refused the request. " + str(e)
            )
        # except Exception as e:
        #     print("\n#RDMS : error in handle_request\n", e)
        #     return None, RequestDeniedError("Geosiris RDMS has refused the request. " + str(e))

    async def handle_put_data_objects(
        self,
        client_info: typing.Union[None, ClientInfo],
        put_data_objects: PutDataObjects,
    ) -> (PutDataObjectsResponse, ETPError):
        print(client_info.ip, ":", "@handle_put_data_objects ")
        files_to_ingest = []
        # parsed_uris = []

        response = []

        for uri in put_data_objects.data_objects:
            data_obj = put_data_objects.data_objects[uri]
            if isinstance(data_obj, dict):
                data_obj = DataObject.get_instance(data_obj)

            files_to_ingest.append((data_obj.data.decode(), "f.xml"))
            # print(client_info.ip, ":", "### ", uri)
            parsed_uri = parse_uri(uri)
            dataspace_name = None
            try:
                None
            except:
                pass
            try:
                dataspaceUri.dataspace
            except:
                pass
            data_manager = dataspaces_handler.get_data_manager(dataspace_name)

            response.append(
                await ingest_xml(
                    file_content=data_obj.data.decode(),
                    file_name=parsed_uri.uuid + ".xml",
                    data_manager=data_manager,
                )
            )

        put_response_map = {}
        for uri in response:
            put_response_map[uri] = PutResponse(
                created_contained_object_uris=[uri]
            )

        return PutDataObjectsResponse(success=put_response_map), None

    async def handle_get_deleted_resources(
        self,
        client_info: typing.Union[None, ClientInfo],
        get_deleted_resources: GetDeletedResources,
    ) -> (GetDeletedResourcesResponse, ETPError):
        print(client_info.ip, ":", "@handle_get_deleted_resources ")
        dataspaceUri = parse_uri(get_deleted_resources.dataspace_uri)
        deleteTimeFilter = get_deleted_resources.delete_time_filter
        dataObjectTypes = get_deleted_resources.data_object_types

        dataspace_name = None
        try:
            None
        except:
            pass
        try:
            dataspaceUri.dataspace
        except:
            pass
        data_manager = dataspaces_handler.get_data_manager(dataspace_name)

        deleted_resources = []
        for res in get_deleted_objects(
            dm=data_manager,
            time_filter=deleteTimeFilter,
            dataObjectTypes=dataObjectTypes,
        ):
            deleted_resources.append(
                DeletedResource(
                    uri=res["uri"],
                    data_object_type=res["dataObjectType"],
                    deleted_time=int(res["deletedTime"]),
                    custom_data={},
                )
            )

        return (
            GetDeletedResourcesResponse(deleted_resources=deleted_resources),
            None,
        )

    async def handle_delete_data_objects(
        self,
        client_info: typing.Union[None, ClientInfo],
        delete_data_objects: DeleteDataObjects,
    ) -> (DeleteDataObjectsResponse, ETPError):
        uris = delete_data_objects.uris
        uuidList = []

        mapUuidToUri = {}
        uri_deleted_objects = []
        for uri_id in uris:
            uri = uris[uri_id]
            parsed_context_uri = parse_uri(uri)
            if isinstance(parsed_context_uri, DataObjectURI):
                obj_uuid = parsed_context_uri.uuid
                uuidList.append(obj_uuid)
                mapUuidToUri[obj_uuid] = uri
            elif len(uri) > 0:
                uuidList.append(uri)
                mapUuidToUri[uri] = uri

            dataspace_name = None
            try:
                parsed_context_uri.dataspace
            except:
                pass
            data_manager = dataspaces_handler.get_data_manager(dataspace_name)

            uri_deleted_objects += await delete_objects(uuidList, data_manager)
            print(
                client_info.ip,
                ":",
                "#DeleteDataObjects --> remove on map : ",
                mapUuidToUri,
            )

        # myobj = {'requesttype': 'deletedataobject', 'uuid': json.dumps(uuidList)}
        # response = requests.post(self.url + "/" + self.requestPage, data=myobj)

        delete_response_map = {}
        for idx in range(0, len(uri_deleted_objects)):
            if uri_deleted_objects[idx]:
                print(
                    client_info.ip,
                    ":",
                    "#DeleteDataObjects --> getting uri for "
                    + uri_deleted_objects[idx],
                )
                # uri = mapUuidToUri[]
                delete_response_map[uri] = ArrayOfString(
                    values=[uri_deleted_objects[idx]]
                )

        return (
            DeleteDataObjectsResponse(deleted_uris=delete_response_map),
            None,
        )

    async def handle_get_data_objects(
        self,
        client_info: typing.Union[None, ClientInfo],
        get_data_objects: GetDataObjects,
    ) -> (GetDataObjectsResponse, ETPError):
        print(client_info.ip, ":", "@handle_get_data_objects")
        uris = get_data_objects.uris
        # res_format = get_data_objects.format
        # print(client_info.ip, ":", "#>># uri", get_data_objects)

        data_obj_res_map = {}

        for uri_id in uris:
            uri = uris[uri_id]
            parsed_context_uri = parse_uri(uri)
            # print(client_info.ip, ":", "### uri", uri, " -- ", parsed_context_uri)
            uuid = ""
            if isinstance(parsed_context_uri, DataObjectURI):
                uuid = parsed_context_uri.uuid
            elif len(uri) > 0:
                uuid = uri

            dataspace_name = None
            try:
                parsed_context_uri.dataspace
            except:
                pass
            data_manager = dataspaces_handler.get_data_manager(dataspace_name)

            data = data_manager.xml_manager.get_data(uuid=uuid)
            if data and data["Body"]:
                xml_content = data["Body"].read()
                # print(client_info.ip, ":", "UUID : ", type(to_Uuid(pyUUID.UUID('{'+uuid+'}'))))
                # uuid, obj_type, version = read_energyml_uuid_type_version(xml_content.decode())
                version = data_manager.xml_manager.get_object_last_versions(
                    uuid
                )
                obj_type = data_manager.xml_manager.get_object_tags(
                    uuid, version
                )[
                    "obj_type"
                ]  # TODO : faire des varibles gloables pour les tags
                if "." in obj_type:
                    obj_type = obj_type.split(".")[1]

                obj_type = refactor_object_type(obj_type)

                # graph_obj = request_objects(type_filter=[obj_type], att_filter=[("Uuid", uuid), ("_version", version)], only_last_version=False)[0]
                graph_obj = data_manager.graph_manager.get_document(
                    collection_name=obj_type, document_key=uuid + "." + version
                )
                resource_obj = self._get_resource_from_rdms_object(graph_obj)

                # print(client_info.ip, ":", "graph_obj ", graph_obj)

                if get_data_objects.format == "json":
                    data_obj_res_map[uuid] = DataObject(
                        blob_id=to_Uuid(pyUUID.UUID("{" + uuid + "}")),
                        format="json",
                        data=json.dumps(graph_obj[obj_type]),
                        resource=resource_obj,
                    )
                else:
                    data_obj_res_map[uuid] = DataObject(
                        blob_id=to_Uuid(pyUUID.UUID("{" + uuid + "}")),
                        format="xml",
                        data=xml_content,
                        resource=resource_obj,
                    )

            else:
                # TODO: faire la liste des exceptions
                pass

        return GetDataObjectsResponse(data_objects=data_obj_res_map), None

    async def handle_get_resources(
        self,
        client_info: typing.Union[None, ClientInfo],
        etp_get_resources: GetResources,
    ) -> (GetResourcesResponse, ETPError):
        # print(client_info.ip, ":", "@handle_get_resources")
        uri = etp_get_resources.context.uri
        req_answer = []
        depth = etp_get_resources.context.depth

        try:
            dataObjectTypes = etp_get_resources.context.data_object_types

            if (
                not uri or uri.lower() == "eml:///"
            ):  # pas de filtre, on garde tout
                # myobj = {"requesttype": "listobjects"}
                data_manager = dataspaces_handler.get_data_manager()
                # r = requests.post(self.url + "/" + self.requestPage, data=myobj)
                req_answer = request_objects(
                    dm=data_manager, type_filter=dataObjectTypes
                )
                # req_answer = json.loads(r.text)
            else:
                # myobj = {"requesttype": "listobjects"}

                parsed_context_uri = parse_uri(uri)

                dataspace_name = None
                try:
                    parsed_context_uri.dataspace
                except:
                    pass

                # eml:///dataspace('test')
                # TODO : faire le cas d'une uri simple dataspace et non dataObject !!

                data_manager = dataspaces_handler.get_data_manager(
                    dataspace_name
                )
                print(
                    client_info.ip,
                    ":",
                    "URI ",
                    parsed_context_uri,
                    " \nfrom ",
                    uri,
                )

                if isinstance(parsed_context_uri, DataObjectURI):
                    obj_type = refactor_object_type(
                        parsed_context_uri.object_type
                    )
                    obj_uuid = parsed_context_uri.uuid
                    include_self = (
                        "self" in str(etp_get_resources.scope).lower()
                    )
                    up = "sources" not in str(etp_get_resources.scope).lower()
                    down = (
                        "targets" not in str(etp_get_resources.scope).lower()
                    )
                    depth = etp_get_resources.context.depth

                    version = (
                        data_manager.xml_manager.get_object_last_versions(
                            obj_uuid
                        )
                    )
                    # obj_type = data_manager.xml_manager.get_object_tags(uuid, version)["obj_type"]
                    req_answer = get_firp_connected_objects(
                        dm=data_manager,
                        uuid=obj_uuid,
                        obj_type=obj_type,
                        version=version,
                        depth=depth,
                        outcomming=up,
                        incoming=down,
                        include_self=include_self,
                    )
                    print(
                        client_info.ip,
                        ":",
                        "get_firp_connected_objects",
                        req_answer,
                        "\ndataspace_name ",
                        dataspace_name,
                        "\ndata_manager",
                        data_manager,
                        "obj_type",
                        obj_type,
                        "\n",
                        "obj_uuid",
                        obj_uuid,
                        "\n",
                        "include_self",
                        include_self,
                        "\n",
                        "up",
                        up,
                        "\n",
                        "down",
                        down,
                        "\n",
                        "depth",
                        depth,
                        "\n",
                    )
                elif isinstance(parsed_context_uri, DataspaceUri):
                    print(parsed_context_uri.dataspace)
                else:
                    print(
                        client_info.ip,
                        ":",
                        "@ETPDataBridge#handle_get_resources : Unkown URI type",
                    )

                # req_answer = json.loads(requests.post(self.url + "/" + self.requestPage, data=myobj).text)

            # navigableEdges = None
            # if "navigableEdges" in etp_get_resources.context:
            #     etp_get_resources.context.navigableEdges

            # filtre sur les types
            # if dataObjectTypes and len(dataObjectTypes):
            #     dataObjectTypes = [obj_type.lower() for obj_type in dataObjectTypes]
            #     try:
            #         filtered = []
            #         for obj in req_answer:
            #             found = False
            #             for obj_t in dataObjectTypes:
            #                 if obj_t in obj.dataObjectType.lower():
            #                     found = True
            #                     break
            #             if found:
            #                 filtered.append(obj)

            #         req_answer = filtered

            #     except KeyError:
            #         print(client_info.ip, ":", "@ETPDataBridge#handle_get_resources : KeyError", req_answer[0])
        except Exception as e:
            raise e

        return self._get_get_resources_response_from_json(
            req_answer
        )  # _get_get_resources_response_from_json retourne deja l'erreur

    async def handle_get_supported_types(
        self,
        client_info: typing.Union[None, ClientInfo],
        get_supported_types: GetSupportedTypes,
    ) -> GetSupportedTypesResponse:
        uri = get_supported_types.uri
        count = get_supported_types.count_objects

        # ETP_SUPPORTED_TYPES

        supported_type_list = []

        obj_type_list = []

        # On commence par lister les objets selon l'uri
        if uri == "eml:///":
            data_manager = dataspaces_handler.get_data_manager()
            obj_map = (
                data_manager.xml_manager.list_bucket_objects_count_versions_and_tags()
            )

            for obj_uuid in obj_map:
                obj = obj_map[obj_uuid]
                supported_type_list.append(
                    SupportedType(
                        data_object_type=obj["obj_type"],
                        object_count=(obj["count"] if count else None),
                    )
                )
                obj_type_list.append(obj["obj_type"])

        else:
            include_self = "self" in str(get_supported_types.scope).lower()
            out = "sources" not in str(get_supported_types.scope).lower()
            incom = "targets" not in str(get_supported_types.scope).lower()

            parsed_context_uri = parse_uri(uri)
            dataspace_name = None
            try:
                parsed_context_uri.dataspace
            except:
                pass
            data_manager = dataspaces_handler.get_data_manager(dataspace_name)

            if isinstance(parsed_context_uri, DataObjectURI):
                obj_uuid = parsed_context_uri.uuid
                obj_type = parsed_context_uri.object_type
                obj_type = refactor_object_type(obj_type)

                obj_last_version = get_last_object_version(
                    dm=data_manager, obj_type=obj_type, uuid=obj_uuid
                )
                if obj_last_version:
                    obj_id = (
                        (obj_type if "Obj_" not in obj_type else obj_type[4:])
                        + "/"
                        + obj_uuid
                        + "."
                        + obj_last_version
                    )
                    obj_map_count = count_distinct_accessible_objects_per_type(
                        dm=data_manager,
                        start_obj_id=obj_id,
                        depth=-1,
                        outcomming=out,
                        incoming=incom,
                        include_self=include_self,
                    )
                    for obj in obj_map_count:
                        print(client_info.ip, ":", "OBJ ", obj)
                        if (
                            not obj["isVoider"]
                            or get_supported_types.return_empty_types
                        ):
                            obj_count = obj["count"]
                            if obj["isVoider"]:
                                obj_count = 0
                            supported_type_list.append(
                                SupportedType(
                                    data_object_type=obj["type"],
                                    object_count=obj_count if count else None,
                                )
                            )
                            obj_type_list.append(obj["type"])
                else:
                    return None, NotFoundError()
            else:
                return None, NotFoundError()

        # on rempli avec les objets supportes mais non presents sur le server
        if get_supported_types.return_empty_types:
            for obj_type in ETP_SUPPORTED_TYPES:
                if obj_type not in obj_type_list:
                    supported_type_list.append(
                        SupportedType(
                            data_object_type=obj_type,
                            object_count=(0 if count else None),
                        )
                    )

        return (
            GetSupportedTypesResponse(supported_types=supported_type_list),
            None,
        )

    async def handle_delete_dataspaces(
        self,
        client_info: typing.Union[None, ClientInfo],
        delete_dataspaces: DeleteDataspaces,
    ) -> (DeleteDataspacesResponse, ETPError):
        dataspace_to_remove = []
        for d_uri in delete_dataspaces.uris.values():
            # TODO : Store changes in dataspaces to have the "last_changed"
            try:
                parsed_uri = parse_uri(d_uri)
                dataspace_name = parsed_uri.dataspace
                print(client_info.ip, ":", ">> ", dataspace_name, ": ")

                if not DataspaceDB.get_dataspace(
                    dataspace_name=dataspace_name
                ):
                    return None, NotFoundError()
                dataspace_to_remove.append(dataspace_name)
            except Exception as e:
                print(client_info.ip, ":", e)
                return None, NotFoundError()

        for d_name in dataspace_to_remove:
            has_been_deleted = DataspaceDB.delete_dataspace(
                dataspace_name=d_name
            )
            print(client_info.ip, ":", has_been_deleted, ": ", d_name)
            if not has_been_deleted:
                return None, NotFoundError()

        dataspaces_handler.update()
        return DeleteDataspacesResponse(success={}), None

    async def handle_get_dataspaces(
        self,
        client_info: typing.Union[None, ClientInfo],
        get_dataspaces: GetDataspaces,
    ) -> (GetDataspacesResponse, ETPError):
        dataspaces = DataspaceDB.get_dataspaces()

        dataspaces_res = []
        for d in dataspaces:
            # TODO : Store changes in dataspaces to have the "last_changed"
            ds = Dataspace(
                uri="eml:///dataspace('" + d.name + "')",
                last_changed=0,
                path="",
                custom_data={},
            )
            dataspaces_res.append(ds)

        return GetDataspacesResponse(dataspaces=dataspaces_res), None

    async def handle_put_dataspaces(
        self,
        client_info: typing.Union[None, ClientInfo],
        put_dataspaces: PutDataspaces,
    ) -> (PutDataspacesResponse, ETPError):
        default_dataspace = DataspaceDB.get_default_dataspace()

        for d in put_dataspaces.dataspaces.values():
            parsed_uri = parse_uri(d.uri)
            dataspace_name = parsed_uri.dataspace
            if not DataspaceDB.get_dataspace(dataspace_name):
                default_dataspace.name = dataspace_name
                default_dataspace.data_store.db_name = dataspace_name + "_xml"
                default_dataspace.data_store.bucket_name = dataspace_name
                default_dataspace.data_graph.db_name = dataspace_name
                default_dataspace.data_graph.graph_name = "g_" + dataspace_name
                default_dataspace.data_deleted.db_name = (
                    dataspace_name + "_deleted"
                )

                DataspaceDB.create_dataspace(default_dataspace)

        dataspaces_handler.update()
        return PutDataspacesResponse(success={}), None

    def _get_resource_from_rdms_object(self, rdms_obj) -> Resource:
        # TODO: revoir la fonction
        # print(client_info.ip, ":", "RDMS Obj", rdms_obj)
        map_resource = {}

        for r_att, r_att_type in get_class_attributes(Resource):
            r_att_lw = r_att.lower()
            find = False
            for etp_obj_att in rdms_obj:
                # print(client_info.ip, ":", "etp_obj_att ", etp_obj_att)
                if r_att_lw == etp_obj_att.lower():
                    find = True
                    if (
                        r_att_lw == "lastchanged"
                        or r_att_lw == "lastmodified"
                        or r_att_lw == "storelastwrite"
                    ):
                        # si on doit convertir une date en entier
                        map_resource[r_att] = self._convert_date_str_to_int(
                            rdms_obj[etp_obj_att]
                        )
                    else:
                        map_resource[r_att] = rdms_obj[etp_obj_att]
                    break

            # si pas trouve on met une valeur par defaut
            if not find or map_resource[r_att] == "":
                # print(client_info.ip, ":", "Setting default value for attribute : ", r_att)
                if (
                    r_att_type.startswith("typing.List")
                    or "array" in r_att_type
                ):
                    map_resource[r_att] = []
                elif r_att_type.startswith("typing.Map"):
                    map_resource[r_att] = {}
                elif r_att_type.startswith("typing.Union"):
                    if "NoneType" in r_att_type:
                        map_resource[r_att] = None
                    else:
                        # print(client_info.ip, ":", "@ETPDataBridge#_get_get_resources_response_from_json : unkown type : " + r_att_type, "for attribute", r_att)
                        pass
                elif "str" in r_att_type:
                    map_resource[r_att] = ""
                elif "bytes" in r_att_type:
                    map_resource[r_att] = b""
                elif "int" in r_att_type:
                    map_resource[r_att] = 0
                # elif "object" == r_att_type:
                # map_resource[r_att] = None
                else:
                    # print(client_info.ip, ":", "@ETPDataBridge#_get_get_resources_response_from_json : unkown type : " + r_att_type, "for attribute", r_att)
                    pass

            # if r_att in map_resource:
            #     print(client_info.ip, ":", "=> Value of ", r_att, "is : '", map_resource[r_att], "' with type ", r_att_type)
            # else:
            #     print(client_info.ip, ":", "no value for (", r_att, ",", r_att_type, ")")

        # on a fini de chercher les attribut dans la reponse, on cree la resource
        # print(client_info.ip, ":", "Try create instance Resource : with map : ", map_resource)

        res = Resource.parse_obj(map_resource)
        # print(client_info.ip, ":", "Created resources : ", res)
        return res

    def _get_get_resources_response_from_json(
        self, json_data_list
    ) -> (GetResourcesResponse, ETPError):
        resource_list = []
        for etp_obj in json_data_list:
            resource_instance = self._get_resource_from_rdms_object(etp_obj)
            # print(client_info.ip, ":", "Ress : ", resource_instance)
            resource_list.append(resource_instance)

        return (
            GetResourcesResponse.parse_obj({"resources": resource_list}),
            None,
        )

    def _convert_date_str_to_int(self, date: str) -> int:
        try:
            return int(datetime)  # on essaie conversion brute
        except:
            try:
                return int(
                    datetime.datetime.strptime(
                        date, "%Y-%m-%dT%H:%M:%S%z"
                    ).timestamp()
                )
            except:
                # print(client_info.ip, ":", "#ERR) non parsed date @_convert_date_str_to_int")
                return 0
