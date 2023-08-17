#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import h5py

from etpclient.utils import (
    search_all_element_value,
    get_xml_dict_from_path,
    get_xml_dict_from_string,
    xml_dict_get_uri,
)

from etptypes.energistics.etp.v12.protocol.data_array.put_data_arrays import (
    PutDataArrays,
)


def descend_obj(obj, sep="\t"):
    """
    Iterate through groups in a HDF5 file and prints the groups and datasets names and datasets attributes
    """
    if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
        for key in obj.keys():
            print(sep, "-", key, ":", obj[key])
            descend_obj(obj[key], sep=sep + "\t")
    elif type(obj) == h5py._hl.dataset.Dataset:
        print("-------------------")
        for key in obj.attrs.keys():
            print(sep + "\t", "-", key, ":", obj.attrs[key])
        print(obj[...])


def h5dump(path, group="/"):
    """
    print HDF5 file metadata

    group: you can give a specific group, defaults to the root group
    """
    with h5py.File(path, "r") as f:
        descend_obj(f[group])


def h5_search_dataset(h5_file_path, path_in_hdf):
    with h5py.File(h5_file_path, "r") as f:
        # _h5_search_dataset_in_obj(f[group])
        dataset = f[path_in_hdf]
        if dataset is not None:
            return dataset[...], dataset.shape, dataset.dtype
    print("Dataset", path_in_hdf, "not found in", h5_file_path)
    return None


def generate_put_data_arrays(
    xml_obj: str, h5_file_path: str, dataspace: str = None
):
    res = []

    obj_dict = get_xml_dict_from_string(xml_obj)
    for path_in_hdf in search_all_element_value(
        obj_dict, "PathInExternalFile"
    ) + search_all_element_value(obj_dict, "PathInHdfFile"):
        print(f"search in h5 {path_in_hdf}")
        data, shape, dtype = h5_search_dataset(h5_file_path, path_in_hdf)
        print(f"\t==> shape {shape}")
        pda_dict = {
            "dataArrays": {
                "0": {
                    "uid": {
                        "uri": xml_dict_get_uri(obj_dict, dataspace),
                        "pathInResource": path_in_hdf,
                    },
                    "array": {
                        "dimensions": list(shape),
                        "data": {"item": {"values": data.flatten().tolist()}},
                    },
                    "customData": {},
                }
            }
        }
        res.append(PutDataArrays.parse_obj(pda_dict))
        # res.append(h5_search_dataset(h5_file_path, path_in_hdf))

    return res
