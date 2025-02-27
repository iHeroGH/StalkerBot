from __future__ import annotations

from collections import defaultdict
import logging
from datetime import datetime as dt
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar

import novus as n
from novus import Embed
from vfflags import Flags

if TYPE_CHECKING:
    from novus.ext import client

from plugins.stalker_utils.upgrade_chat_manager import UpgradeChatManager as uc

from .misc_utils import (get_channel_from_cache, get_guild_from_cache,
                         get_users_from_cache)

log = logging.getLogger("plugins.stalker_utils.stalker_objects")


SpecialKeyword = tuple[str, bool]


class KeywordEnum(IntEnum):
    """
    An Enum class to keep track of the different types of keywords.
    """

    glob = 1
    server_specific = 2
    channel_specific = 3
    special = 4

    def __str__(self) -> str:
        match self:
            case KeywordEnum.glob:
                return "(Global)"

            case KeywordEnum.server_specific:
                return "(Server-Specific)"

            case KeywordEnum.channel_specific:
                return "(Channel-Specific)"

            case KeywordEnum.special:
                return "(Special)"

            case _:
                return ""


class Keyword:
    """
    The Keyword class keeps track of a user's keywords and its type (via the
    KeywordEnum class)

    Attributes
    ----------
    keyword : str
        The keyword text itself
    keyword_type : KeywordEnum, default=KeywordEnum.global
        The type of the keyword. Global by default.
    server_id : int, default=0
        The ID of the server for this Keyword. 0 if none is provided
    channel_id : int, default=0
        The ID of the channel for this Keyword. 0 if none is provided
    whitelist : list[SpecialKeyword] | None, default=None
        Each word from whitelist must be present in the content, the bool
        denotes whether the word must be exactly matched or not
    blacklist : list[SpecialKeyword] | None, default=None
        None of the words from blacklist can be present in the content, the
        bool denotes whether the word must be exactly matched or not
    """

    def __init__(
                self,
                keyword: str,
                keyword_type: KeywordEnum = KeywordEnum.glob,
                server_id: int = 0,
                channel_id: int = 0,
                whitelist: list[SpecialKeyword] | None = None,
                blacklist: list[SpecialKeyword] | None = None
            ) -> None:
        """Initializes a Keyword object"""
        if not Keyword.validate_keyword(
                    keyword_type,
                    keyword,
                    server_id,
                    channel_id,
                    whitelist,
                    blacklist
                ):
            raise ValueError(
                "The provided parameters do not create a valid Keyword " +
                f"({keyword} {keyword_type} {server_id} {channel_id} " +
                f"{whitelist} {blacklist})"
            )

        self.keyword = keyword
        self.keyword_type = keyword_type
        self.server_id = server_id
        self.channel_id = channel_id
        self.whitelist = whitelist
        self.blacklist = blacklist

    @staticmethod
    def validate_keyword(
                keyword_type: KeywordEnum,
                keyword: str,
                server_id: int,
                channel_id: int,
                whitelist: list[SpecialKeyword] | None,
                blacklist: list[SpecialKeyword] | None
            ) -> bool:

        match keyword_type:
            case KeywordEnum.glob:
                # Only keyword is given
                return bool(keyword) and not (
                    server_id or channel_id or
                    whitelist is not None or blacklist is not None
                )
            case KeywordEnum.server_specific:
                # Keyword and server ID are given
                return bool(
                    keyword and server_id and not channel_id and
                    whitelist is None and blacklist is None
                )
            case KeywordEnum.channel_specific:
                # Keyword and channel ID are given
                return bool(
                    keyword and not server_id and channel_id and
                    whitelist is None and blacklist is None
                )
            case KeywordEnum.special:
                # Nothing given except whitelist and blacklist
                return bool(
                    not keyword and
                    whitelist is not None and blacklist is not None
                )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Keyword)
            and
            self.keyword == other.keyword
        )

    def __lt__(self, other: object) -> bool:
        return (
            isinstance(other, Keyword)
            and
            self.keyword < other.keyword
        )

    def __hash__(self) -> int:
        return hash((
            self.keyword,
            self.keyword_type,
            self.server_id,
            self.channel_id,
            tuple(self.whitelist) if self.whitelist is not None else None,
            tuple(self.blacklist) if self.blacklist is not None else None
        ))

    @classmethod
    def from_record(cls, record) -> Keyword:
        try:
            return cls(
                keyword=record['keyword'],
                server_id=record['server_id']
            )
        except KeyError:
            raise KeyError("Invalid Keyword record passed to `from_record`.")

    def get_list_identifier(self) -> str:
        return self.keyword + (
                f" ({str(self.keyword_type)} - {self.server_id})"
                if self.keyword_type == KeywordEnum.server_specific else ""
            ) + (
                f" ({str(self.keyword_type)} - {self.channel_id})"
                if self.keyword_type == KeywordEnum.channel_specific else ""
            )

    def __repr__(self) -> str:
        return (
            f"Keyword("
            f"{self.keyword=}, "
            f"{self.keyword_type=}, "
            f"{self.server_id=}, "
            f"{self.channel_id=}, "
            f"{self.whitelist=}, "
            f"{self.blacklist=})"
        )

    def __str__(self) -> str:
        if self.keyword_type == KeywordEnum.special:
            assert self.whitelist is not None and self.blacklist is not None
            return str(self.whitelist) + " " + str(self.blacklist)
        else:
            return self.keyword


class FilterEnum(IntEnum):
    """
    An Enum class to keep track of the different types of filters.
    Currently, there are text, user, channel, and server filters.
    """

    text_filter = 1
    user_filter = 2
    channel_filter = 3
    server_filter = 4

    def __str__(self) -> str:
        match self:
            case FilterEnum.text_filter:
                return "(Text)"

            case FilterEnum.user_filter:
                return "(User)"

            case FilterEnum.channel_filter:
                return "(Channel)"

            case FilterEnum.server_filter:
                return "(Server)"

            case _:
                return ""


class Filter:
    """
    The Filter class keeps track of a filter and its type (via the
    FilterEnum class)
    """

    bot: client.Client | None = None

    def __init__(
                self,
                filter: str | int,
                filter_type: FilterEnum = FilterEnum.text_filter
            ) -> None:
        """Initializes a Filter object"""
        self.filter = filter
        self.filter_type = filter_type

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Filter)
            and
            self.filter == other.filter
            and
            self.filter_type == other.filter_type
        )

    def __lt__(self, other: object) -> bool:
        return (
            isinstance(other, Filter)
            and
            type(self.filter) is type(other.filter)
            and
            self.filter < other.filter  # type: ignore
        )

    def __hash__(self) -> int:
        return self.__repr__().__hash__()

    def __repr__(self) -> str:
        return str(self.filter) + " " + str(self.filter_type)

    async def get_list_identifier(
            self,
            guild_id: int | None = None,
            user: n.GuildMember | int | None = None,
            md: str = "`", mention: bool = True) -> str:

        match self.filter_type:
            case FilterEnum.user_filter:
                user = user or (await get_users_from_cache(
                        self.bot, [self.filter], guild_id
                    ))[0]

                return self.get_object_identifier(user, md, mention)

            case FilterEnum.channel_filter:
                channel = get_channel_from_cache(self.bot, self.filter)
                return self.get_object_identifier(channel, md, mention)

            case FilterEnum.server_filter:
                server = get_guild_from_cache(self.bot, self.filter)
                return self.get_object_identifier(server, md, mention)

            case _:  # Text filters
                return f"{md}{self.filter}{md}"

    def get_object_identifier(
                self,
                object: n.Channel | n.GuildMember | n.BaseGuild | int | None,
                md: str = "`", mention: bool = True
            ) -> str:
        """Gets a formatted str for a Channel, Member, or Guild"""
        if object and not isinstance(object, int):
            if not mention or isinstance(object, n.BaseGuild):
                return f"{md}{str(object)}{md} ({object.id})"
            else:
                return f"{object.mention} ({object.id})"
        else:  # Object not in cache
            return f"{md}{self.filter}{md}"


class Settings(Flags):
    """The Settings class keeps track of a user's settings as Flags."""

    if TYPE_CHECKING:
        self_trigger: bool
        quote_trigger: bool
        reply_trigger: bool
        bot_trigger: bool
        edit_trigger: bool
        embed_message: bool

    CREATE_FLAGS: ClassVar[dict[str, int]] = {
        "self_trigger": 1 << 0,  # The user triggers their own triggers
        "quote_trigger": 1 << 1,  # Keywords in a "> text" quote are triggered
        "reply_trigger": 1 << 2,  # The user recieves a DM for replies
        "bot_trigger": 1 << 3,  # Bots and webhooks trigger user keywords
        "edit_trigger": 1 << 4,  # Messages that get edited re-trigger
        "embed_message": 1 << 5,  # Messages sent to the user are embedded
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
            self_trigger=False,
            quote_trigger=True,
            reply_trigger=False,
            bot_trigger=False,
            edit_trigger=True,
            embed_message=True
        )

    @classmethod
    def from_record(cls, record) -> Settings:
        try:
            return cls(
                self_trigger=record['self_trigger'],
                quote_trigger=record['quote_trigger'],
                reply_trigger=record['reply_trigger'],
                bot_trigger=record['bot_trigger'],
                edit_trigger=record['edit_trigger'],
                embed_message=record['embed_message']
            )
        except KeyError:
            raise KeyError("Invalid Settings record passed to `from_record`.")


class Stalker:
    """
    A Stalker object is a user who uses StalkerBot!

    This class keeps track of a user's keywords, filters, settings, bot muting,
    and opting out.
    """

    MAX_KEYWORDS = 5

    def __init__(
                self,
                user_id: int,
                keywords: dict[KeywordEnum, set[Keyword]] = {
                    KeywordEnum.glob: set(),
                    KeywordEnum.server_specific: set(),
                    KeywordEnum.channel_specific: set()
                },
                filters: dict[FilterEnum, set[Filter]] = {
                    FilterEnum.text_filter: set(),
                    FilterEnum.user_filter: set(),
                    FilterEnum.channel_filter: set(),
                    FilterEnum.server_filter: set()
                },
                settings: Settings = Settings.default(),
                mute_until: dt | None = None,
                opted_out: bool = False,
                dm_channel: int | n.Channel | None = None
            ) -> None:
        """Initializes a Stalker object"""
        self.user_id: int = user_id
        self.keywords: dict[KeywordEnum, set[Keyword]] = keywords
        self.filters: dict[FilterEnum, set[Filter]] = filters
        self.settings: Settings = settings
        self.mute_until: dt | None = mute_until
        self.opted_out: bool = opted_out
        self.dm_channel = dm_channel

    def clear(self):
        self.keywords = {
                    KeywordEnum.glob: set(),
                    KeywordEnum.server_specific: set(),
                    KeywordEnum.channel_specific: set()
                }
        self.filters = {
                    FilterEnum.text_filter: set(),
                    FilterEnum.user_filter: set(),
                    FilterEnum.channel_filter: set(),
                    FilterEnum.server_filter: set()
                }
        self.settings = Settings.default()
        self.mute_until = None
        self.opted_out = False

        return self

    async def format_keywords(self, bot: client.Client) -> Embed:
        """Returns a formatted Embed listing a user's keywords"""

        add_command = bot.get_command("keyword add")
        command_mention = "`keyword add`"
        if add_command:
            command_mention = add_command.mention

        embed = Embed(title="Keywords", color=0xFEE75C)

        if not self.used_keywords:
            embed.description = (
                "You don't have any keywords! " +
                f"Set some up by running the {command_mention} command."
            )
            return embed

        embed.description = (
            "You are using " +
            f"{self.used_keywords}/{await self.max_keywords} keywords"
        )

        # Having a 0 key is guaranteed
        embed.add_field(
            name="__Global Keywords__",
            value=(
                '- `' +
                '`\n- `'.join(
                    map(str, sorted(self.keywords[KeywordEnum.glob]))
                ) + "`"
                if self.keywords[KeywordEnum.glob] else
                "You don't have any global keywords! " +
                f"Set some up by running the {command_mention} command."
            ),
            inline=False
        )

        server_keyword_map: dict[int, set[Keyword]] = defaultdict(set)
        server_specific_text = ""
        for keyword in self.keywords[KeywordEnum.server_specific]:
            server_keyword_map[keyword.server_id].add(keyword)

        for server_id, keyword in server_keyword_map.items():
            # If we can't find the guild in cache, let the user know
            server = get_guild_from_cache(bot, server_id)
            server_specific_text += (
                f"**{server.name}** ({server.id})" if server else
                f"**{server_id}** *(StalkerBot may not be in this server)*"
            ) + "\n"

            server_specific_text += '- `' + '`\n- `'.join(
                map(str, sorted(server_keyword_map[server_id]))
            ) + "`\n"

        channel_keyword_map: dict[int, set[Keyword]] = defaultdict(set)
        channel_specific_text = ""
        for keyword in self.keywords[KeywordEnum.channel_specific]:
            channel_keyword_map[keyword.channel_id].add(keyword)

        for channel_id, keyword in channel_keyword_map.items():
            # If we can't find the guild in cache, let the user know
            channel = get_channel_from_cache(bot, channel_id)
            channel_specific_text += (
                f"**{channel.name}** ({channel.id})" if channel else
                f"**{channel_id}** *(StalkerBot may not be in this channel)*"
            ) + "\n"

            channel_specific_text += '- `' + '`\n- `'.join(
                map(str, sorted(channel_keyword_map[channel_id]))
            ) + "`\n"

        embed.add_field(
            name="__Server-Specific Keywords__",
            value=(
                server_specific_text
                if server_specific_text else
                "You don't have any server-specific keywords! " +
                f"Set some up by running the {command_mention} command."
            ),
            inline=False
        )

        embed.add_field(
            name="__Channel-Specific Keywords__",
            value=(
                channel_specific_text
                if channel_specific_text else
                "You don't have any channel-specific keywords! " +
                f"Set some up by running the {command_mention} command."
            ),
            inline=False
        )

        return embed

    async def format_filters(
                self,
                bot: client.Client,
                guild_id: int | None = None
            ) -> Embed:
        """Returns a formatted Embed listing a user's filters"""

        FILTER_TITLES = {
            FilterEnum.text_filter: "Text Filters",
            FilterEnum.user_filter: "User Filters",
            FilterEnum.channel_filter: "Channel Filters",
            FilterEnum.server_filter: "Server Filters",
        }

        FILTER_COMMAND_NAMES = {
            FilterEnum.text_filter: "filter add text",
            FilterEnum.user_filter: "filter add user",
            FilterEnum.channel_filter: "filter add channel",
            FilterEnum.server_filter: "filter add server"
        }

        # So we can check cache later
        Filter.bot = bot

        embed = Embed(title="Filters", color=0xFEE75C)
        for filter_type, title in FILTER_TITLES.items():

            # Get the command mention for easy access for the user
            filter_mention = f"`{FILTER_COMMAND_NAMES[filter_type]}`"
            filter_command = bot.get_command(FILTER_COMMAND_NAMES[filter_type])
            if filter_command:
                filter_mention = filter_command.mention

            filter_list = sorted(list(self.filters[filter_type]))
            if filter_type == FilterEnum.user_filter:
                users = await get_users_from_cache(
                    bot,
                    [filter.filter for filter in filter_list],
                    guild_id
                )
                users.sort(
                    key=lambda x:
                    x.username if isinstance(x, n.GuildMember) else str(x)
                )

                filter_list = list(zip(filter_list, users))
            else:
                filter_list = list(zip(filter_list, [None] * len(filter_list)))

            pre = '- ' if not filter_type == FilterEnum.text_filter else ''
            sep = '\n- ' if not filter_type == FilterEnum.text_filter else ', '

            embed.add_field(
                name=f"__{title}__",
                value=(
                    pre +
                    sep.join(
                        [
                            await f.get_list_identifier(guild_id, user_o)
                            for f, user_o in filter_list
                        ]
                    ) if self.filters[filter_type]
                    else
                    f"*You don't have any {title.lower()}! " +
                    f"Set some up by running the {filter_mention} command.*"
                ),
                inline=False
            )

        return embed

    @property
    def used_keywords(self) -> int:
        return sum([len(i) for i in self.keywords.values()])

    @property
    async def max_keywords(self) -> int:

        additional_keywords: int = uc.get_orders(self.user_id)
        override = {
            342529068907888643: 5,
            204439680727384064: 5,
            322542134546661388: 50,
            141231597155385344: 95
        }

        return (
            self.MAX_KEYWORDS + additional_keywords +
            override.get(self.user_id, 0)
        )

    def represent_channel(self) -> str:
        if isinstance(self.dm_channel, int):
            return str(self.dm_channel)
        if isinstance(self.dm_channel, n.Channel):
            return str(self.dm_channel.id)

        return "?"

    def __repr__(self) -> str:
        return (
            "Stalker(" +
            f"user_id={self.user_id}, "
            f"channel_id={self.represent_channel()}, "
            f"keywords={self.keywords}, "
            f"filters={self.filters}, "
            f"settings={self.settings}, "
            f"mute_until={self.mute_until}, "
            f"opted_out={self.opted_out})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(self.user_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Stalker) and other.user_id == self.user_id
