from typing import TYPE_CHECKING

from datetime import datetime as dt, timedelta as td

from novus.enums.utils import Enum
from vfflags import Flags

class Keyword:
    """
    The Keyword class keeps track of a user's keywords. It also stores
    a Keywords server_id, if it is a server-specific keyword. If the server_id
    is 0, then it is a global keyword.

    Attributes
    ----------
    keyword : str
        The keyword text itself
    server_id : int
        The ID of the server for this Keyword (default 0, global)
    """

    def __init__(
                self,
                keyword: str,
                server_id: int = 0
            ) -> None:
        """Initializes a Keyword object (default Global)"""
        self.keyword = keyword
        self.server_id = server_id

class FilterEnum(Enum):
    """
    An Enum class to keep track of the different types of filters.
    Currently, there are text, user, channel, and server filters.
    """

    text_filter = 1
    user_filter = 2
    channel_filter = 3
    server_filter = 4

class Filter:
    """
    The Filter class keeps track of a filter and its type (via the
    FilterEnum class)
    """

    def __init__(
                self,
                filter: str | int,
                filter_type: FilterEnum = FilterEnum.text_filter
            ) -> None:
        """Initializes a Filter object"""
        self.filter = filter
        self.filter_type  = filter_type

class Settings(Flags):
    """The Settings class keeps track of a user's settings as Flags."""

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
        "edit_trigger": 1 << 4, # Messages with a keyword that get edited re-trigger
        "embed_message": 1 << 5, # Messages sent to the user are embedded
    }

class Stalker:
    """
    A Stalker object is a user who uses StalkerBot!

    This class keeps track of a user's keywords, filters, settings, bot muting,
    and opting out.
    """

    def _init__(
                self,
                keywords: list[Keyword],
                filters: list[Filter],
                settings: Settings,
                mute_until: dt | None = None,
                is_opted: bool = False
            ) -> None:
        """Initializes a Stalker object"""
        self.keywords = keywords
        self.filters = filters
        self.settings = settings
        self.mute_until = mute_until
        self.is_opted = is_opted

    @classmethod
    def from_records(cls):
        ...