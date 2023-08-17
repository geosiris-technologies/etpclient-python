#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import json
import datetime

from etptypes.energistics.etp.v12.protocol.data_array import *
from etptypes.energistics.etp.v12.datatypes import *
from etptypes.energistics.etp.v12.datatypes.data_array_types import *
from etpproto.uri import *

from etpproto.error import ETPError
import logging
import h5pyd


class HSDSBridge:
    def __init__(self, asset: str):
        self.asset = asset
        # self.username = HSDS_USERNAME
        # self.password = HSDS_PASSWORD
        # self.endpoint = HSDS_ENDPOINT
        # self.bucket   = HSDS_BUCKET
        # self.domain   = HSDS_DOMAIN_PREFIX+self.asset+".h5"

    def handle_metadata(self, etp_req: GetDataArrayMetadata):
        dataArrays = etp_req.data_arrays
        arrayMetadata = {}

        for key, value in dataArrays.items():
            fin = None
            try:

                fin = h5pyd.File(
                    self.domain,
                    mode="r",
                    endpoint=self.endpoint,
                    username=self.username,
                    password=self.password,
                    bucket=self.bucket,
                    use_cache=True,
                )
            except IOError as ioe:
                if ioe.errno == 403:
                    logging.error(
                        "No read access to domain: {}".format(self.domain)
                    )
                elif ioe.errno == 404:
                    logging.error(
                        "Domain: {} not found : {}".format(self.domain, ioe)
                    )
                elif ioe.errno == 410:
                    logging.error(
                        "Domain: {} has been recently deleted".format(
                            self.domain
                        )
                    )
                else:
                    logging.error(
                        "Error opening domain {}: {}".format(self.domain, ioe)
                    )

            if fin:
                dataset = fin[value.path_in_resource]
                if dataset:
                    arrayMetadata[key] = DataArrayMetadata(
                        dimensions=list(dataset.shape),
                        array_type=AnyArrayType.ARRAY_OF_FLOAT,
                    )

        return GetDataArrayMetadataResponse(array_metadata=arrayMetadata), None

    def send_request(self, etp_req):
        if isinstance(etp_req, GetDataArrays):
            return self.send_get_data_arrays(etp_req)
        elif isinstance(etp_req, GetDataSubarrays):
            return self.send_get_data_subarrays(etp_req)
        elif isinstance(etp_req, PutDataArrays):
            return self.send_put_data_arrays(etp_req)
        else:
            print("#HSDSBridge can not handle request of type ", type(etp_req))
            return None, None

    def send_get_data_arrays(
        self, get_data_arrays: GetDataArrays
    ) -> (GetDataArraysResponse, ETPError):
        dataArrays = get_data_arrays.data_arrays

        dataArraysResponse = {}

        for key, value in dataArrays.items():
            # uri = DataObjectURI(value['uri'])

            # search ExternalPartReference in the database
            # take the filename as domain
            # domain = "/home/geosiris/test/"+external_part.filename
            fin = None
            try:

                fin = h5pyd.File(
                    self.domain,
                    mode="r",
                    endpoint=self.endpoint,
                    username=self.username,
                    password=self.password,
                    bucket=self.bucket,
                    use_cache=True,
                )
            except IOError as ioe:
                if ioe.errno == 403:
                    logging.error(
                        "No read access to domain: {}".format(self.domain)
                    )
                elif ioe.errno == 404:
                    logging.error(
                        "Domain: {} not found : {}".format(self.domain, ioe)
                    )
                elif ioe.errno == 410:
                    logging.error(
                        "Domain: {} has been recently deleted".format(
                            self.domain
                        )
                    )
                else:
                    logging.error(
                        "Error opening domain {}: {}".format(self.domain, ioe)
                    )

            if fin:
                dataset = fin[value.path_in_resource]
                print("dataset : ", type(list(dataset[()].flatten())))
                data = AnyArray(
                    item=ArrayOfFloat(values=list(dataset[()].flatten()))
                )
                dataArraysResponse[key] = DataArray(
                    dimensions=list(dataset.shape), data=data
                )

        return GetDataArraysResponse(data_arrays=dataArraysResponse), None
        # {"test": DataArray(dimensions=[1],data=AnyArray(item=b"000000"))}

    def send_get_data_subarrays(
        self, get_data_arrays: GetDataSubarrays
    ) -> (GetDataSubarraysResponse, ETPError):
        dataSubarrays = get_data_arrays.data_subarrays

        dataSubarraysResponse = {}

        for key, value in dataSubarrays.items():
            print(value)
            array = value.uid
            starts = value.starts
            counts = value.counts
            stop = list(map(lambda x, y: x + y, starts, counts))

            slices = []
            for i in range(len(starts)):
                slices.append(slice(starts[i], stop[i]))

            print(slices)
            # uri = DataObjectURI(value['uri'])

            # search ExternalPartReference in the database
            # take the filename as domain
            # domain = "/home/geosiris/test/"+external_part.filename

            fin = None
            try:

                fin = h5pyd.File(
                    self.domain,
                    mode="r",
                    endpoint=self.endpoint,
                    username=self.username,
                    password=self.password,
                    bucket=self.bucket,
                    use_cache=True,
                )
            except IOError as ioe:
                if ioe.errno == 403:
                    logging.error(
                        "No read access to domain: {}".format(self.domain)
                    )
                elif ioe.errno == 404:
                    logging.error(
                        "Domain: {} not found : {}".format(self.domain, ioe)
                    )
                elif ioe.errno == 410:
                    logging.error(
                        "Domain: {} has been recently deleted".format(
                            self.domain
                        )
                    )
                else:
                    logging.error(
                        "Error opening domain {}: {}".format(self.domain, ioe)
                    )

            if fin:
                dataset = fin[array.path_in_resource]
                subdataset = dataset[tuple(slices)]
                data = AnyArray(item=ArrayOfFloat(values=subdataset.flatten()))
                dataSubarraysResponse[key] = DataArray(
                    dimensions=list(subdataset.shape), data=data
                )

        return (
            GetDataSubarraysResponse(data_subarrays=dataSubarraysResponse),
            None,
        )

    def send_put_data_arrays(
        self, put_data_arrays: PutDataArrays
    ) -> (PutDataArraysResponse, ETPError):
        dataArrays = put_data_arrays.data_arrays

        dataArraysResponse = {}

        for key, value in dataArrays.items():
            print(value)
            path = value.uid.path_in_resource
            da = value.array
            print(da.data.item.values)
            print(da.dimensions)
            fin = None
            try:

                fin = h5pyd.File(
                    self.domain,
                    mode="a",
                    endpoint=self.endpoint,
                    username=self.username,
                    password=self.password,
                    bucket=self.bucket,
                    use_cache=True,
                )
            except IOError as ioe:
                if ioe.errno == 403:
                    logging.error(
                        "No read access to domain: {}".format(self.domain)
                    )
                elif ioe.errno == 404:
                    logging.error(
                        "Domain: {} not found : {}".format(self.domain, ioe)
                    )
                elif ioe.errno == 410:
                    logging.error(
                        "Domain: {} has been recently deleted".format(
                            self.domain
                        )
                    )
                else:
                    logging.error(
                        "Error opening domain {}: {}".format(self.domain, ioe)
                    )

            if fin:
                try:
                    eda = fin.create_dataset(
                        name=path,
                        shape=da.dimensions,
                        data=da.data.item.values,
                    )
                    print(eda[()])
                    # fin[path] = eda
                    dataArraysResponse[key] = "true"
                except:
                    dataArraysResponse[key] = "false"

        return PutDataArraysResponse(success=dataArraysResponse), None
