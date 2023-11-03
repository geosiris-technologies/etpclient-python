#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import re
from lxml import etree


def get_class_attributes(cls):
    att_and_type_list = []
    props = cls.schema()
    if "properties" in props:
        props = props["properties"]
        for p_name in props:
            att_and_type_list.append(
                (p_name, props[p_name]["type"])  # props[p_name]['title'],
            )
    return att_and_type_list


def refactor_object_type(obj_type: str):
    if obj_type.lower().startswith("obj_"):
        return obj_type[4:]
    return obj_type


##################


def parse_schema_version(schema_version: str):
    return (
        re.compile(r'([^"]*[a-zA-Z\s])?([0-9][0-9\.]*)$')
        .search(schema_version)
        .group(2)
    )


def parse_schema_version_flat(schema_version: str):
    return parse_schema_version(schema_version).replace(".", "")[:2]


def energyml_namespace_to_pkg_name(namespace):
    if re.match(r".*common(v2)?$", namespace):
        return "eml"
    elif re.match(r".*prodml(v2)?$", namespace):
        return "prodml"
    elif re.match(r".*resqml(v2)?$", namespace):
        return "resqml"
    elif re.match(r".*witsml(v2)?$", namespace):
        return "witsml"
    return "unkown_type"


# =========================


def get_xml_dict_from_path(file_path: str):
    with open(file_path, "r") as f:
        return get_xml_dict_from_string(f.read())
    return None


def get_xml_dict_from_string(file_content: str):
    return xml_tree_to_dict(get_xml_tree_string(file_content))


def get_xml_tree_from_path(file_path: str):
    with open(file_path, "r") as f:
        return get_xml_tree_string(f.read())
    return None


def get_xml_tree_string(file_content):
    try:
        return etree.fromstring(
            bytes(bytearray(file_content, encoding="utf-8"))
        )
    except Exception:
        return etree.fromstring(file_content)


##################
#   ______
#  /_  __/_______  ___     ____ ______________  __________
#   / / / ___/ _ \/ _ \   / __ `/ ___/ ___/ _ \/ ___/ ___/
#  / / / /  /  __/  __/  / /_/ / /__/ /__/  __(__  |__  )
# /_/ /_/   \___/\___/   \__,_/\___/\___/\___/____/____/


def xml_get_namespace(tree):
    return tree.nsmap[tree.prefix]


def xml_get_type(tree):
    tag = tree.tag
    if "}" in tag:
        tag = tag[tag.rindex("}") + 1 :]
    return tag


def xml_get_attrib(tree, attrib_name, wild=True):
    for k in tree.attrib:
        if (wild and k.lower() == attrib_name.lower()) or (
            not wild and k == attrib_name
        ):
            return tree.attrib[k]
    return None


def xml_get_schema_version_flat(tree):
    return parse_schema_version_flat(xml_get_attrib(tree, "schemaVersion"))


def xml_get_schema_version(tree):
    return parse_schema_version(xml_get_attrib(tree, "schemaVersion"))


def xml_get_obj_version(tree):
    obj_version = xml_get_attrib(tree, "objectVersion")
    if obj_version is not None:
        return obj_version
    return "0"


def xml_get_uuid(tree):
    return xml_get_attrib(tree, "uuid")


def xml_get_data_object_type(tree):
    return (
        energyml_namespace_to_pkg_name(xml_get_namespace(tree))
        + xml_get_schema_version_flat(tree)
        + "."
        + xml_get_type(tree)
    )


#     ____  _      __
#    / __ \(_)____/ /_
#   / / / / / ___/ __/
#  / /_/ / / /__/ /_
# /_____/_/\___/\__/


def xml_dict_get_namespace(tree_dict):
    return get_direct_child_from_tag(tree_dict, "_namespace")[0]


def xml_dict_get_type(tree_dict):
    return get_direct_child_from_tag(tree_dict, "_type")[0]


def xml_dict_get_uuid(tree_dict):
    return get_direct_child_from_tag(tree_dict, "uuid")[0]


def xml_dict_get_schema_version_flat(tree_dict):
    return parse_schema_version_flat(
        get_direct_child_from_tag(tree_dict, "schemaVersion")[0]
    )


def xml_dict_get_schema_version(tree_dict):
    return parse_schema_version(
        get_direct_child_from_tag(tree_dict, "schemaVersion")[0]
    )


def xml_dict_get_obj_version(tree_dict):
    obj_version = get_direct_child_from_tag(tree_dict, "objectVersion")[0]
    if obj_version is not None:
        return obj_version
    return "0"


def xml_dict_get_data_object_type(tree_dict):
    return (
        energyml_namespace_to_pkg_name(xml_dict_get_namespace(tree_dict))
        + xml_dict_get_schema_version_flat(tree_dict)
        + "."
        + xml_dict_get_type(tree_dict)
    )


def xml_dict_get_uri(tree_dict, dataspace_name=None):
    return (
        "eml:///"
        + (
            "dataspace('" + dataspace_name + "')/"
            if dataspace_name is not None and len(dataspace_name) > 0
            else ""
        )
        + xml_dict_get_data_object_type(tree_dict)
        + "("
        + xml_dict_get_uuid(tree_dict)
        + ")"
    )


def xml_tree_to_dict(tree, root=True):
    """
    Convert an lxml.etree node tree into a dict.
    """
    result = {}

    if root:
        result["_namespace"] = tree.nsmap[tree.prefix]
        result["_type"] = tree.tag
        if "}" in result["_type"]:
            result["_type"] = result["_type"][
                result["_type"].rindex("}") + 1 :
            ]

    for attribute_key, attribute_value in tree.items():
        # log("attribute", attribute)
        attribute_key = (
            attribute_key.split("}")[1]
            if "}" in attribute_key
            else attribute_key
        )
        result[attribute_key] = attribute_value

    for element in tree.iterchildren():
        # Remove namespace prefix
        key = element.tag.split("}")[1] if "}" in element.tag else element.tag

        # Process element as tree element if the inner XML contains non-whitespace content
        if element.text and element.text.strip():
            value = element.text
        else:
            value = xml_tree_to_dict(element, root=False)
        if key in result:
            if type(result[key]) is list:
                result[key].append(value)
            else:
                tempvalue = None
                try:
                    tempvalue = result[key].copy()
                except:
                    tempvalue = str(result[key])
                result[key] = [tempvalue, value]
        else:
            result[key] = value
    return result


def search_element_has_child(tree_dict, child_name: str, wild=True) -> list:
    result = []
    try:
        if isinstance(tree_dict, list):
            for child in tree_dict:
                result = result + search_element_has_child(
                    child, child_name, wild
                )
        else:
            for child_key in tree_dict.keys():
                key = re.sub(r"({[^}]+})(.*)", r"\2", child_key)
                # log(indent*"\t", "childName = " + key, "[", child_key, "]")
                if (wild and key.lower() == child_name.lower()) or (
                    key == child_name
                ):
                    result.append(tree_dict)
                result = result + search_element_has_child(
                    tree_dict[child_key], child_name, wild
                )
    except Exception:
        pass
    return result


def get_direct_child_from_tag(tree_dict, child_tag: str, wild=True):
    result = []
    try:
        if isinstance(tree_dict, list):
            for child in tree_dict:
                result = result + search_element_has_child(
                    child, child_tag, wild
                )
        else:
            for child_key in tree_dict.keys():
                key = re.sub(r"({[^}]+})(.*)", r"\2", child_key)
                # log("childName = " + key, "[", child_key, "]")
                if (wild and key.lower() == child_tag.lower()) or (
                    key == child_tag
                ):
                    result.append(tree_dict[child_key])
    except Exception:
        pass
    return result


def search_all_element_value(tree_dict, child_name: str, wild=True) -> list:
    result = []
    try:
        if isinstance(tree_dict, list):
            for child in tree_dict:
                result = result + search_all_element_value(
                    child, child_name, wild
                )
        else:
            for child_key in tree_dict.keys():
                key = re.sub(r"({[^}]+})(.*)", r"\2", child_key)
                # log(indent*"\t", "childName = " + key, "[", child_key, "]")
                if (wild and key.lower() == child_name.lower()) or (
                    key == child_name
                ):
                    result.append(tree_dict[child_key])
                result = result + search_all_element_value(
                    tree_dict[child_key], child_name, wild
                )
    except Exception:
        pass
    return result


def find_child_from_tag(tree_dict, child_tag: str, wild=True):
    return get_direct_child_from_tag(
        search_element_has_child(tree_dict, child_tag, wild), child_tag, wild
    )
