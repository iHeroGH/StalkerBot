from __future__ import annotations

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

    @classmethod
    def from_record(cls, record) -> Keyword:
        try:
            return cls(
                keyword = record['keyword'],
                server_id = record['server_id']
            )
        except KeyError:
            raise KeyError("Invalid Keyword record passed to `from_record`.")

    def __repr__(self) -> str:
        return f"Keyword(keyword={self.keyword}, server_id={self.server_id})"

    def __str__(self) -> str:
        return ("Global" if not self.server_id else "Server-Specific"
                + f" Keyword `{self.keyword}`"
                + f" at {self.server_id}" if self.server_id else "")

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

    def __repr__(self) -> str:
        return f"Filter(filter={self.filter}, filter_type={self.filter_type})"

    def __str__(self) -> str:
        return self.__repr__()

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

    def __str__(self) -> str:

        flag_strings = [
            f"{flag}={self.__getattribute__(flag)}, "
            for flag in self.VALID_FLAGS
            ]

        return f"Settings({''.join(flag_strings)})"

    @classmethod
    def default(cls) -> Settings:
        return cls(
            self_trigger = False,
            quote_trigger = True,
            reply_trigger = True,
            bot_trigger = False,
            edit_trigger = True,
            embed_message = True
        )

    @classmethod
    def from_record(cls, record) -> Settings:
        try:
            return cls(
                self_trigger = record['self_trigger'],
                quote_trigger = record['quote_trigger'],
                reply_trigger = record['reply_trigger'],
                bot_trigger = record['bot_trigger'],
                edit_trigger = record['edit_trigger'],
                embed_message = record['embed_message']
            )
        except KeyError:
            raise KeyError("Invalid Settings record passed to `from_record`.")

class Stalker:
    """
    A Stalker object is a user who uses StalkerBot!

    This class keeps track of a user's keywords, filters, settings, bot muting,
    and opting out.
    """

    def __init__(
                self,
                keywords: list[Keyword] = [],
                filters: list[Filter] = [],
                settings: Settings = Settings.default(),
                mute_until: dt | None = None,
                is_opted: bool = False
            ) -> None:
        """Initializes a Stalker object"""
        self.keywords = keywords
        self.filters = filters
        self.settings = settings
        self.mute_until = mute_until
        self.is_opted = is_opted

    def __repr__(self) -> str:
        return (f"Stalker("+
                f"keywords={self.keywords}, "
                f"filters={self.filters}, "
                f"settings={self.settings}, "
                f"mute_until={self.mute_until}, "
                f"is_opted={self.is_opted})"
            )

    def __str__(self) -> str:
        return self.__repr__()