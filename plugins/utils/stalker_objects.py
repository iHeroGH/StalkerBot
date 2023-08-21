from typing import TYPE_CHECKING

from novus.enums.utils import Enum
from vfflags import Flags

class Keyword:

    def __init__(
                self,
                keyword,
                server_id: int = 0
            ) -> None:
        self.keyword = keyword
        self.server_id = server_id

class FilterEnum(Enum):
    text_filter = 1
    user_filter = 2
    channel_filter = 3
    server_filter = 4

class Filter:

    def __init__(
            self,
            filter,
            filter_type: FilterEnum = FilterEnum.text_filter
        ) -> None:
        self.filter = filter
        self.filter_type  = filter_type

class Settings(Flags):

    if TYPE_CHECKING:
        self_trigger: bool
        quote_trigger: bool
        reply_trigger: bool
        bot_trigger: bool
        edit_trigger: bool
        embed_message: bool

    CREATE_FLAGS = {
        "self_trigger": 1 << 0, # The user triggers their own triggers
        "quote_trigger": 1 << 1, # Keywords in a "> text" quote are triggered
        "reply_trigger": 1 << 2, # The user recieves a DM for replies
        "bot_trigger": 1 << 3, # Bots and webhooks trigger user keywords
        "edit_trigger": 1 << 4, # A message with a keyword that gets editted re-triggers
        "embed_message": 1 << 5, # Messages sent to the user are embedded
    }

class Stalker:

    def _init__(
            self,
            keywords: list[Keyword],
            filters: list[Filter],
            settings: Settings,
            is_blacklisted: bool = False,
            is_opted: bool = False
        ):

        self.keywords = keywords
        self.filters = filters
        self.settings = settings
        self.is_blacklisted = is_blacklisted
        self.is_opted = is_opted


