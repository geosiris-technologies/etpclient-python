#
# Copyright (c) 2022-2023 Geosiris.
# SPDX-License-Identifier: Apache-2.0
#
import os
from typing import List, Dict

from fastavro import reader, schemaless_reader, schemaless_writer, writer
from etptypes import avro_schema
import json
import sys
import websocket
import asyncio
import logging

try:
    import thread
except ImportError:
    import _thread as thread

import time
from datetime import datetime

from etpproto.connection import ETPConnection, ConnectionType
from etpproto.client_info import ClientInfo
from etpproto.messages import Message

import etpclient.etp.serverprotocols

from etpclient.etp.requester import request_session
from etpclient.utils import basic_auth_encode, basic_auth_header


async def wait_for_response(
    conn: ETPConnection, websocket_manager, msg_id: int, timeout: int = 5
):
    delta_t = 0.01
    begining = datetime.now()
    while (datetime.now() - begining).seconds < timeout:
        # if (websocket_manager.recieved_msg_dict):
        #     logging.debug("##----##")
        #     logging.debug(websocket_manager.recieved_msg_dict)

        if msg_id in websocket_manager.recieved_msg_dict and (
            isinstance(websocket_manager.recieved_msg_dict[msg_id], Message)
            or (
                isinstance(websocket_manager.recieved_msg_dict[msg_id], list)
                and websocket_manager.recieved_msg_dict[msg_id][
                    -1
                ].is_final_msg()
            )
        ):
            return websocket_manager.recieved_msg_dict[msg_id]
        await asyncio.sleep(delta_t)
    # logging.debug("@Ws : ", websocket_manager.recieved_msg_dict)
    # logging.debug("@Ws : ")
    # logging.debug(websocket_manager.recieved_msg_dict)
    return None


class WebSocketManager:
    def __init__(
        self,
        uri: str,
        username: str = None,
        password: str = None,
        token: str = None,
        additional_headers: Dict = None
    ):
        self.closed = False
        self.recieved_msg_dict = {}
        self.connected = False
        logging.debug(f"Connecting to {uri}")

        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        elif username is not None:
            headers["Authorization"] = "Basic " + basic_auth_encode(username, password)

        # headers["data-partition-id"] = "osdu"
        # logging.debug(f"additional_headers {additional_headers}")
        if isinstance(additional_headers, dict):
            headers = headers | additional_headers
        elif isinstance(additional_headers, list):
            for a_h in additional_headers or []:
                headers = headers | a_h

#         logging.debug(f"Headers {headers}")

        self.ws = websocket.WebSocketApp(
            uri,
            subprotocols=[ETPConnection.SUB_PROTOCOL],
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        # if token:
        #     logging.debug("auth bearer : \n" + "authorization: Bearer " + token)
        #     self.ws = websocket.WebSocketApp(
        #         uri,
        #         subprotocols=[ETPConnection.SUB_PROTOCOL],
        #         header=["authorization: Bearer " + token],
        #         on_open=self.on_open,
        #         on_message=self.on_message,
        #         on_error=self.on_error,
        #         on_close=self.on_close,
        #     )
        # elif username and password:
        #     self.ws = websocket.WebSocketApp(
        #         uri,
        #         subprotocols=[ETPConnection.SUB_PROTOCOL],
        #         header=[basic_auth_header(username, password)],
        #         on_open=self.on_open,
        #         on_message=self.on_message,
        #         on_error=self.on_error,
        #         on_close=self.on_close,
        #     )
        # else:
        #     self.ws = websocket.WebSocketApp(
        #         uri,
        #         subprotocols=[ETPConnection.SUB_PROTOCOL],
        #         on_open=self.on_open,
        #         on_message=self.on_message,
        #         on_error=self.on_error,
        #         on_close=self.on_close,
        #     )

        self.etp_connection = ETPConnection(
            connection_type=ConnectionType.CLIENT,
            client_info=ClientInfo(
                ip=uri,
                endpoint_capabilities={
                    "MaxWebSocketFramePayloadSize": 900000,
                    "MaxWebSocketMessagePayloadSize": 900000,
                },
            ),
        )
        self.recieved = {}

        def run(websocket):
            websocket.ws.run_forever()
            logging.debug("thread terminating...")
            websocket.etp_connection.is_connected = False

        thread.start_new_thread(run, (self,))

    def is_connected(self):
        # logging.debug(self.etp_connection)
        # return self.etp_connection.is_connected
        return self.etp_connection.is_connected and not self.closed

    def on_message(self, ws, message):
        # logging.debug("ON_MSG : ")
        logging.debug(f"ON_MSG : {message}")

        async def handle_msg(
            conn: ETPConnection, websocket_manager, msg: bytes
        ):
            try:
                # logging.debug("##> before recieved " )
                recieved = Message.decode_binary_message(
                    msg,
                    dict_map_pro_to_class=ETPConnection.generic_transition_table,
                )
                if recieved.is_final_msg():
                    logging.debug(f"\n##> recieved header : {recieved.header}")
                    # logging.debug("\n##> recieved body : ", recieved.body, "\n\n")
                    # if (
                    #     recieved.header.protocol == 0
                    #     or type(recieved.body) != bytes
                    # ):
                    # logging.debug("ERR : ", recieved.body)
                    logging.debug(f"##> body type : {type(recieved.body)}")
                    # logging.debug("##> body content : ", recieved.body)

                    # msg = await conn.decode_partial_message(recieved)

                    # logging.debug("##> msg " )
                if msg:
                    async for b_msg in conn.handle_bytes_generator(msg):
                        pass
                        # logging.debug(b_msg)
                        # if (
                        #     b_msg.headers.correlation_id
                        #     not in websocket_manager.recieved_msg_dict[
                        #         b_msg.headers.correlation_id
                        #     ]
                        # ):
                        #     websocket_manager.recieved_msg_dict[
                        #         b_msg.headers.correlation_id
                        #     ] = [0]
                        # websocket_manager.recieved_msg_dict[
                        #     b_msg.headers.correlation_id
                        # ].append(b_msg)
                    if (
                        recieved.header.correlation_id
                        not in websocket_manager.recieved_msg_dict
                    ):
                        websocket_manager.recieved_msg_dict[
                            recieved.header.correlation_id
                        ] = []
                    websocket_manager.recieved_msg_dict[
                        recieved.header.correlation_id
                    ].append(recieved)
            except Exception as e:
                logging.error(f"#ERR: {type(e).__name__}")
                logging.error(f"#Err: {msg}")
                raise e

        asyncio.run(handle_msg(self.etp_connection, self, message))

    def on_error(self, ws, error):
        logging.debug("ON_ERR")
        try:
            logging.debug(error)
        except Exception as e:
            logging.debug(e)

    def on_close(self, ws, a, b):
        # logging.debug("ON_CLOSE")
        self.closed = True
        try:
            logging.info(f"### closed ###\n{a}\n{b}")
            sys.stdout.flush()
            self.etp_connection.is_connected = False
            sys.exit(1)
        except Exception as e:
            logging.error(e)

    def on_open(self, ws):
        # logging.debug("OPENING")
        self.connected = True
        try:
            answer = asyncio.run(self.send_and_wait(request_session(), 4.0))
            logging.info(f"CONNECTED : {answer}")
        except Exception as e:
            logging.error(e)

    async def send_raw(self, msg: bytes):
        self.ws.send(msg)

    async def send_and_wait(self, req, timeout: int = 5):
        # logging.debug("SENDING " + str(req))
        # logging.debug("SENDING NW")
        # await self.logging.debug_message(req)
        obj_msg = Message.get_object_message(etp_object=req)

        msg_id = -1
        async for (
            m_id,
            msg_to_send,
        ) in self.etp_connection.send_msg_and_error_generator(obj_msg, None):
            self.ws.send(msg_to_send, websocket.ABNF.OPCODE_BINARY)
            msg_id = m_id
            # logging.debug(f"@WS: [{m_id}] {obj_msg}")
            logging.debug(f"@WS: [{m_id}]")
            logging.debug(obj_msg)
            # logging.debug("Msg sent... ", msg_to_send)
        # return wait_for_response(conn=self.etp_connection, msg_id = msg_id, timeout=timeout)
        result = await wait_for_response(
            conn=self.etp_connection,
            websocket_manager=self,
            msg_id=msg_id,
            timeout=timeout,
        )
        # logging.debug("Answer : \n", result)
        # logging.debug("Answer recieved")
        return result

    async def send_no_wait(self, req, timeout: int = 5):
        # logging.debug("SENDING NW" + str(req))
        # logging.debug("SENDING NW")
        # await self.logging.debug_message(req)

        msg_id_list = []
        msg_id = -1
        async for (
            msg_id,
            msg_to_send,
        ) in self.etp_connection.send_msg_and_error_generator(
            Message.get_object_message(etp_object=req), None
        ):
            self.ws.send(msg_to_send, websocket.ABNF.OPCODE_BINARY)
            msg_id_list.append(msg_id)

        return msg_id_list

    async def print_message(self, req):
        try:
            # Writing
            with open("test_unserialAvro_header.avro", "wb") as out:
                schemaless_writer(
                    out,
                    json.loads(avro_schema(type(req))),
                    req.dict(by_alias=True),
                )
            logging.debug("====== header ======")
            # Reading
            with open("test_unserialAvro_header.avro", "rb") as fo:
                r_dict = schemaless_reader(
                    fo, json.loads(avro_schema(type(req)))
                )
                for record in r_dict:
                    logging.debug(f"{record}: {r_dict[record]}")
        finally:
            os.remove("test_unserialAvro_header.avro")
