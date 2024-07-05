import os
import re
import traceback
import urllib
from pathlib import Path
from typing import Any, Optional, List

import numpy as np
import requests
import enum

from etpproto.uri import parse_uri

from etpclient.etp.h5_handler import write_h5
from etpclient.server_config import *
from etpclient.utils import search_all_element_value


class HttpMethod(enum.Enum):
    DELETE = enum.auto()
    GET = enum.auto()
    PATCH = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()


class RequestError(Exception):
    def __init__(self, message="Failed to send request."):
        self.message = message
        super().__init__(self.message)


def search_h5_paths(obj: dict):
    return search_all_element_value(obj, "PathInHdfFile") + search_all_element_value(obj, "PathInExternalFile")


def get_token_from_config(
        config: ServerConfig,
):
    print(config.get_config())
    token_url = config.get(SERVER_TOKEN_URL, None)
    if token_url is not None:
        return get_token(
            url=token_url,
            client_id=config.get("CLIENT_ID"),
            client_secret=config.get("CLIENT_SECRET"),
            headers=config.get_headers(),
            scope=config.get(SERVER_TOKEN_SCOPE),
            refresh_token=config.get(SERVER_TOKEN_REFRESH_TOKEN),
            grant_type=config.get(SERVER_TOKEN_GRANT_TYPE),
        )


def get_token(
        url: str,
        client_id: str,
        client_secret: str,
        headers: dict,
        scope: Optional[str],
        refresh_token: Optional[str],
        grant_type: Optional[str] = "client_credentials",
):
    params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "scope": scope,
            "grant_type": grant_type,
        }
    print(f"params {params}")
    return EtpRestClient._send_request(
        url=url,
        method=HttpMethod.POST,
        headers=headers,
        params=params,
        data=params,
    ).json()["access_token"]


class EtpRestClient:

    def __init__(self, host: str, headers: dict = None, data_partition_id: str = None, bearer_token: str = None):
        host = re.sub("ws?://", "http://", host)
        host = re.sub("wss?://", "https://", host)
        if not host.startswith("http"):
            if bearer_token is not None:
                host = f"https://{host}"
            else:
                host = f"http://{host}"
        self.host = host
        self.headers = headers or {}
        if data_partition_id is not None:
            self.headers["data-partition-id"] = data_partition_id
        self.bearer_token = bearer_token

    # {{RESERVOIR_DDMS_HOST}}/dataspaces
    def get_dataspaces(self):
        return EtpRestClient.make_request(
            method=HttpMethod.GET,
            url=f"{self.host}/dataspaces",
            add_headers=self.headers,
            bearer_token=self.bearer_token,
        )

    # {{RESERVOIR_DDMS_HOST}}/dataspaces/{{DATASPACE_ID}}/resources/all
    def get_resources(self, dataspace_id: str):
        return EtpRestClient.make_request(
            method=HttpMethod.GET,
            url=f"{self.host}/dataspaces/{urllib.parse.quote(dataspace_id, safe='')}/resources/all",
            add_headers=self.headers,
            bearer_token=self.bearer_token,
        )

    # {{RESERVOIR_DDMS_HOST}}/dataspaces/{{DATASPACE_ID}}/resources/{{DATA_OBJECT_TYPE}}/{{DATA_OBJECT_TYPE_GUID}}
    def get_dataobject(self,
                       dataspace_id: str,
                       data_object_type: str,
                       data_object_type_guid: str,
                       format: str = "xml"
                       ):
        url = f"{self.host}/dataspaces/{urllib.parse.quote(dataspace_id, safe='')}/resources/{urllib.parse.quote(data_object_type, safe='')}/{urllib.parse.quote(data_object_type_guid, safe='')}"
        print(f"url: {url}")
        return EtpRestClient.make_request(
            method=HttpMethod.GET,
            url=url,
            params={"$format": format},
            add_headers=self.headers,
            bearer_token=self.bearer_token,
        )

    def get_dataobject_from_uri(self, uri: str, format: str = "xml"):
        o_uri = parse_uri(uri)
        return self.get_dataobject(
            dataspace_id=o_uri.dataspace,
            data_object_type=f"{o_uri.domain}{o_uri.domain_version}.{o_uri.object_type}",
            data_object_type_guid=o_uri.uuid,
            format=format
        )

    def get_dataobject_from_uri_xml(self, uri: str):
        return re.sub(r"</?\s*DataObjects\s*>", "", client.get_dataobject_from_uri(uri=uri, format="xml").text, re.IGNORECASE)

    # {{RESERVOIR_DDMS_HOST}}/dataspaces/{{DATASPACE_ID}}/resources/{{DATA_OBJECT_TYPE}}/{{DATA_OBJECT_TYPE_GUID}}/arrays/{{PATH_IN_RESOURCE}}
    def get_dataarray(self,
                      dataspace_id: str,
                      data_object_type: str,
                      data_object_type_guid: str,
                      path_in_resource: str
                      ):
        url = f"{self.host}/dataspaces/{urllib.parse.quote(dataspace_id, safe='')}/resources/{urllib.parse.quote(data_object_type, safe='')}/{urllib.parse.quote(data_object_type_guid, safe='')}/arrays/{urllib.parse.quote(path_in_resource, safe='')}"
        print(f"URL: {url}")
        return EtpRestClient.make_request(
            method=HttpMethod.GET,
            url=url,
            add_headers=self.headers,
            bearer_token=self.bearer_token,
        )

    def s_download_dataspace(self, dataspace_name: str, output_folder: str, h5_for_each: bool = False, download_h5: bool = True, download_xml: bool = True) -> None:
        self.s_download_objects(list(map(lambda x: x['uri'], self.get_resources(dataspace_name).json())), output_folder, h5_for_each, download_h5, download_xml)

    def s_download_objects(self, uris: List[str], output_folder: str, h5_for_each: bool = False, download_h5: bool = True, download_xml: bool = True) -> None:
        try:
            os.makedirs(output_folder)
        except:
            pass
        uris.reverse()
        for uri in uris:
            o_uri = parse_uri(uri)
            f_path_prefix = f"{output_folder}/{o_uri.domain}{o_uri.domain_version}.{o_uri.object_type}_{o_uri.uuid}"
            print(uri)
            if download_xml:
                data_obj_xml = self.get_dataobject_from_uri_xml(uri=uri)
                try:
                    # p_uri = parse_uri(uri)
                    f_path = Path(f"{f_path_prefix}.xml")
                    with f_path.open("w") as _f:
                        _f.write(data_obj_xml)
                except Exception as e:
                    print(traceback.format_exc())
                    # print(f"\t Exception {e}\n\t{data_obj_xml}")

            # for hdf_dataset_path in data_obj_json
            # if "TriangulatedSetRepresentation" in uri:
            if download_h5 and "Representation" in uri:
                data_obj_json = self.get_dataobject_from_uri(uri=uri, format="json").json()
                try:
                    self.s_download_h5_from_uri(
                        uri=uri,
                        paths_in_resource=search_h5_paths(data_obj_json),
                        h5_path=f"{f_path_prefix}.h5" if h5_for_each else f"{output_folder}/{os.path.basename(os.path.normpath(output_folder))}.h5"
                    )
                except Exception:
                    print(traceback.format_exc())

    def s_download_h5_from_uri(self, uri: str, paths_in_resource: List[str], h5_path: str):
        o_uri = parse_uri(uri)
        return self.s_download_h5(
            dataspace_id=o_uri.dataspace,
            data_object_type=f"{o_uri.domain}{o_uri.domain_version}.{o_uri.object_type}",
            data_object_type_guid=o_uri.uuid,
            paths_in_resource=paths_in_resource,
            h5_path=h5_path
        )

    def s_download_h5(self,
                      dataspace_id: str,
                      data_object_type: str,
                      data_object_type_guid: str,
                      paths_in_resource: List[str],
                      h5_path: str
                      ):
        arrays = {}
        if len(paths_in_resource) > 0:
            for pir in paths_in_resource:
                gda = self.get_dataarray(
                    dataspace_id=dataspace_id,
                    data_object_type=data_object_type,
                    data_object_type_guid=data_object_type_guid,
                    path_in_resource=pir,
                ).json()
                try:
                    array = np.array(
                        gda['data']['data']
                        # dtype=,
                    ).reshape(tuple(gda['data']['dimensions']))
                    arrays[pir] = array
                except Exception as e:
                    print(e)
                    print(gda['data']['data'][:100])
                    print(len(gda['data']['data']))
                    print(gda['data']['dimensions'])
            if len(arrays) > 0:
                write_h5(h5_path=h5_path, arrays=arrays)

    @staticmethod
    def _send_request(method: HttpMethod, url: str, data: Optional[str] = None, headers: Optional[dict] = None,
                       params: Optional[dict] = None) -> requests.Response:
        if method == HttpMethod.DELETE:
            response = requests.delete(url=url, params=params or {}, headers=headers or {}, verify=False)
        elif method == HttpMethod.GET:
            response = requests.get(url=url, params=params or {}, headers=headers or {}, verify=False)
        elif method == HttpMethod.POST:
            response = requests.post(url=url, params=params or {}, data=data, headers=headers or {}, verify=False)
        elif method == HttpMethod.PUT:
            response = requests.put(url=url, params=params or {}, data=data, headers=headers or {}, verify=False)
        return response

    @staticmethod
    def _send_request_with_bearer_token(
            method: HttpMethod,
            url: str,
            data: str,
            headers: dict,
            params: dict,
            bearer_token: str,
            config: Optional[ServerConfig] = None
    ) -> requests.Response:
        if bearer_token is not None and 'Bearer ' not in bearer_token:
            bearer_token = 'Bearer ' + bearer_token
        headers["Authorization"] = bearer_token

        response = EtpRestClient._send_request(method, url, data, headers, params)
        if not response.ok:
            response.raise_for_status()

        return response

    @staticmethod
    def make_request(
            method: HttpMethod,
            url: str,
            data: Any = '',
            add_headers: Optional[dict] = None,
            params: Optional[dict] = None,
            bearer_token: Optional[str] = None,
            no_auth: bool = False
    ) -> requests.Response:

        add_headers = add_headers or {}
        params = params or {}

        headers = {
            'content-type': 'application/json',
        }

        for key, value in add_headers.items():
            headers[key] = value

        if no_auth:
            response = EtpRestClient._send_request(method, url, data, headers, params)
        elif bearer_token:
            response = EtpRestClient._send_request_with_bearer_token(method, url, data, headers, params, bearer_token)
        # elif cls.token_refresher:
        #     response = self._send_request_with_token_refresher(headers, method, url, data, params)
        else:
            raise RequestError()
        return response


if __name__ == "__main__":
    client = EtpRestClient(
        host="prsh.testing.preshiptesting.osdu.aws/api/reservoir-ddms/v2",
        data_partition_id="osdu",
        bearer_token="eyJraWQiOiJ2VDAxeWczNTg4VjJxVHpRRDNKcStNZjErMGJoZjIrS216ejFubjZIK2pZPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5NzJkNDc0Zi1hODFlLTRkMzktOGRkMC1jYWE2MzMzNjJkMTQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0yLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMl9JSFo5UmtPUE8iLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIxaXQyNDFmdjhxbDdvZmxyNmVhcDRtODBxNyIsIm9yaWdpbl9qdGkiOiI0M2M0ZTU3MC1lNWY2LTQzMWEtYWFhNC05MTUwYzI2ZDlmNzkiLCJldmVudF9pZCI6IjdmZWNlMzQxLWI1YmItNGFhOC05MDExLWZlYTE1YzA3NWI0NyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoib3BlbmlkIGVtYWlsIiwiYXV0aF90aW1lIjoxNzE4MDczODIwLCJleHAiOjE3MTgwNzU2MjAsImlhdCI6MTcxODA3MzgyMCwianRpIjoiM2Y0NDI4MjYtODU4Ny00MGY2LWFmNWMtZTg4MWI1NzU0YzY2IiwidXNlcm5hbWUiOiJhZG1pbi1tYWluQHRlc3RpbmcuY29tIn0.IAXux00Lnq8EKf5T3Pq4s3igRVx1orRZcxCDfGOfi5G_DdvKpmMHUAq5YJ7g4j9kfkY4bgw1EX38MKf24tcIfJVs29Js9E8bvD8ZmAH1fZoMHn7D4bdusFuv0u0h_A6ErItDfxCjVdYJNBW7cmegwEOZquSX4OWCFT997HhRBJkPrwRSf2Lf566G5nMXxQgVT8duw3hJhVecYC4FcebIOBmAgLPaLpA_hHshI7dxQFlwiz0GzFTTy_FmCt3yl25yx4S3jByPp-NQ3M7BqlyYpBch5Q7ow281MYvVpUB_Cz-McNvPZHli_3wdVKbXYzS_0ZUe-2UE2vWueAyeal9goA"
    )
    #
    # print(client.get_dataspaces().json())
    # obj = client.get_dataobject_from_uri_xml("eml:///dataspace('F2F/Demo')/resqml20.obj_TriangulatedSetRepresentation(0674295b-128e-4470-ae36-f9eaa4b51fe1)")
    # print(obj)
    #
    # print(search_all_element_value(client.get_dataobject_from_uri("eml:///dataspace('F2F/Demo')/resqml20.obj_TriangulatedSetRepresentation(0674295b-128e-4470-ae36-f9eaa4b51fe1)", "json"), "PathInHdfFile"))
    # # F2F%2FDemo/resources/resqml20.obj_TriangulatedSetRepresentation/0674295b-128e-4470-ae36-f9eaa4b51fe1/arrays/%2FRESQML%2F0674295b-128e-4470-ae36-f9eaa4b51fe1%2Ftriangles_patch0
    # print(client.get_dataarray(
    #     "F2F/Demo",
    #     "resqml20.obj_TriangulatedSetRepresentation",
    #     "0674295b-128e-4470-ae36-f9eaa4b51fe1",
    #     "/RESQML/0674295b-128e-4470-ae36-f9eaa4b51fe1/triangles_patch0"
    # ).json())
    #
    client.s_download_dataspace('F2F/Demo', "out/'F2F_Demo'", False, False, True)
    # # client.s_download_objects(["eml:///dataspace('F2F/Demo')/resqml20.obj_TriangulatedSetRepresentation(0674295b-128e-4470-ae36-f9eaa4b51fe1)"], "out")

    # print(os.path.basename(os.path.normpath("out/coucou/test")))
