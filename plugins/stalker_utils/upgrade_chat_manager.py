import logging

import upgradeChat as uc

log = logging.getLogger("plugins.stalker_utils.upgrade_chat_manager")


class UCInitException(Exception):
    pass


class UpgradeChatManager:

    _UC_CLIENT: uc.API | None = None

    @classmethod
    def _initialize_client(cls, client_id: str, client_secret: str) -> None:
        cls._UC_CLIENT = uc.API(
            client_id,
            client_secret,
            raw=False
        )

    @classmethod
    def get_client(cls):
        if not cls._UC_CLIENT:
            log.error("UpgradeChat was not properly initialized!")
            raise UCInitException("UpgradeChat was not properly initialized!")
        return cls._UC_CLIENT

    @classmethod
    def get_orders(cls, user_id: int) -> int:
        model = cls.get_client().get_orders(discord_id=user_id)
        assert not isinstance(model, dict)

        item_names = [
            item.product.name
            for order in (model.data if model else [])
            for item in (order.order_items if order else [])
        ]

        return sum([
            5
            for name in item_names
            if name == "5x StalkerBot Keywords"
        ])
