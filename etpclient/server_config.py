#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import configparser
import logging
import os
from typing import Optional, Any

import yaml


INI_FILE_PATH = "INI_FILE_PATH"

SERVER_URL = "url"
SERVER_USERNAME = "username"
SERVER_PASSWORD = "password"
SERVER_ADDITIONAL_HEADERS = "additional-headers"
SERVER_TOKEN = "token"
SERVER_TOKEN_URL = "token-url"
SERVER_TOKEN_GRANT_TYPE = "token-grant-type"
SERVER_TOKEN_SCOPE = "token-scope"
SERVER_TOKEN_REFRESH_TOKEN = "token-refresh_token"
USE_REST = "use-rest"


def replace_env_templates(value: Any):
    if isinstance(value, str):
        res = str(value)
        for k, v in os.environ.items():
            res = res.replace("${{" + k + "}}", v)
        return res
    elif isinstance(value, list):
        return [
            replace_env_templates(iv)
            for iv in value
        ]
    elif isinstance(value, dict):
        return {
            k: replace_env_templates(v)
            for k, v in value.items()
        }
    else:
        return value


class ServerConfig:
    _config: dict
    _config_path: str

    def __init__(self, config_path: Optional[str] = None):
        self._config = {}
        self._config_parser = None
        self._config_path = config_path
        if config_path is None:
            self._config_path = os.environ.get(INI_FILE_PATH)

        try:

            if self._config_path.lower().endswith(".ini"):
                self._config_parser = configparser.ConfigParser(os.environ)
                self._config_parser.read(self._config_path)
            else:
                with open(self._config_path) as yaml_file:
                    config = yaml.safe_load(yaml_file)
                    self._config = {}
                    for k in config:
                        self[k] = config[k]
        except IOError as e:
            logging.error("File not found " + str(self._config_path))
            raise e
        except Exception as e:
            logging.exception(e)

    def __contains__(self, key):
        return key in self._config

    def __getitem__(self, key):
        res = None
        if key in self._config:
            res = self._config[key]
        elif self._config_parser is not None:
            res = self._config_parser.get(
                section="environment",
                option=key,
                fallback=os.environ[key] if key in os.environ else None,
            )

        if res is None and key in os.environ:
            res = os.environ[key]
        return replace_env_templates(res)

    def __setitem__(self, key, new_value):
        self._config[key] = new_value

    def get(self, key, default=None):
        return self[key] or default

    def get_config(self) -> dict:
        return replace_env_templates(self._config)

    def get_headers(self):
        return {k: v for h in self.get(SERVER_ADDITIONAL_HEADERS, []) for k, v in h.items()}
