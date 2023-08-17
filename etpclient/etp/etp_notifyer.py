from typing import Any, ClassVar, Mapping

import uuid as pyUUID
from dataclasses import dataclass

from etpproto.client_info import ClientInfo
from etpproto.messages import Message

from etptypes.helpers import AvroModel
from etptypes.energistics.etp.v12.protocol.store_notification import (
    UnsolicitedStoreNotifications,
)
from etptypes.energistics.etp.v12.datatypes.object.subscription_info import (
    SubscriptionInfo,
)
from etptypes.energistics.etp.v12.datatypes.object.context_info import (
    ContextInfo,
)
from etptypes.energistics.etp.v12.datatypes.object.relationship_kind import (
    RelationshipKind,
)
from etptypes.energistics.etp.v12.datatypes.object.context_scope_kind import (
    ContextScopeKind,
)

from gabbro.etp.connection_register import ConnectionRegister


@dataclass
class ETPNotifyer:

    # For each ETPConnection, store a list of notifications subscription
    map_client_to_subscribtion: ClassVar[
        Mapping[ClientInfo, list[AvroModel]]
    ] = {}

    unsolicited_notification: ClassVar[list[AvroModel]] = []

    @classmethod
    async def subscribe(
        cls, client_info: ClientInfo, subscription: Any
    ) -> None:
        print(client_info.ip, ": #ETPNotiyer.subscribe")

        if client_info not in cls.map_client_to_subscribtion:
            cls.map_client_to_subscribtion[client_info] = []

        cls.map_client_to_subscribtion[client_info].append(subscription)

    @classmethod
    async def unsubscribe(
        cls, client_info: ClientInfo, subscription: Any
    ) -> None:
        print(client_info.ip, ": #ETPNotiyer.unsubscribe")
        cls.map_client_to_subscribtion.pop(client_info, None)

    @classmethod
    async def trigger(cls, notif_content: Any):
        print(": #ETPNotiyer.trigger")

        # a notification is recieved from the server after something occured (e.g. a modification)

    @classmethod
    async def _notify(cls, client_info: ClientInfo, msg: bytes):
        print(client_info.ip, ": #ETPNotiyer._notify")
        websocket, connection = ConnectionRegister.get_ws_n_con(client_info)

        if websocket:
            await websocket.send_bytes(msg)
        else:
            print(
                client_info.ip, ": #ETPNotiyer._notify => websocket not found"
            )

    @classmethod
    async def send_unsolicited_notification(cls, client_info: ClientInfo):
        print(
            client_info.ip,
            ": #ETPNotiyer.send_unsolicited_notification : <",
            len(cls.unsolicited_notification),
            ">",
        )
        websocket, connection = ConnectionRegister.get_ws_n_con(client_info)

        for msg in cls.unsolicited_notification:
            m = Message.get_object_message(etp_object=msg)
            print(
                client_info.ip,
                ": sending unsolicited_notification  ",
                m,
                "\n\n",
            )

            async for msg_part in connection.send_msg_and_error_generator(
                m, None
            ):
                await websocket.send_bytes(msg_part)

    @classmethod
    def add_unsolicited_notification(cls, msg: AvroModel):
        cls.unsolicited_notification.append(msg)


u_store_notif = UnsolicitedStoreNotifications(
    subscriptions=[
        SubscriptionInfo(
            context=ContextInfo(
                uri="eml:///", depth=3, navigable_edges=RelationshipKind.BOTH
            ),
            scope=ContextScopeKind.SOURCES,
            request_uuid=pyUUID.uuid4().bytes,
            start_time=0,
            include_object_data=False,
        )
    ]
)
ETPNotifyer.add_unsolicited_notification(msg=u_store_notif)
