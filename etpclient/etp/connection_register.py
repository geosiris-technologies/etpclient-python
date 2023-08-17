from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from etpproto.client_info import ClientInfo
from fastapi import WebSocket


@dataclass
class ConnectionRegister:

    map_connection: ClassVar[Mapping[ClientInfo, WebSocket]] = {}

    @classmethod
    def register(cls, client_info: ClientInfo, websocket: WebSocket) -> None:
        print(client_info.ip, ": #ConnectionRegister.register")
        if client_info in cls.map_connection:
            print(client_info.ip, ": is overriting previous connection")

        cls.map_connection[client_info] = websocket

    @classmethod
    def forget(cls, client_info: ClientInfo) -> None:
        print(client_info.ip, ": #ConnectionRegister.forget")
        cls.map_connection.pop(client_info, None)

    @classmethod
    def get_ws_n_con(cls, client_info: ClientInfo) -> WebSocket:
        print(client_info.ip, ": #ConnectionRegister.get_ws_n_con")
        if client_info in cls.map_connection:
            return cls.map_connection[client_info]
        return None
