from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime as dt

from novus.enums.utils import Enum
from novus import Embed
from vfflags import Flags

import novus as n
if TYPE_CHECKING:
    from novus import types as t
    from novus.ext import client

from .misc import get_guild_from_cache, get_users_from_cache, \
                                    get_channel_from_cache

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
        """Initializes a Keyword object (default global)"""
        self.keyword = keyword
        self.server_id = server_id

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
        return hash(self.keyword)

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
        return self.keyword

class FilterEnum(Enum):
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
                return f"(Text)"

            case FilterEnum.user_filter:
                return f"(User)"

            case FilterEnum.channel_filter:
                return f"(Channel)"

            case FilterEnum.server_filter:
                return f"(Server)"

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
        self.filter_type  = filter_type

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
                type(self.filter) == type(other.filter)
                and
                self.filter < other.filter # type: ignore
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

            case _: # Text filters
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
        else: # Object not in cache
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

    CREATE_FLAGS = {
        "self_trigger": 1 << 0, # The user triggers their own triggers
        "quote_trigger": 1 << 1, # Keywords in a "> text" quote are triggered
        "reply_trigger": 1 << 2, # The user recieves a DM for replies
        "bot_trigger": 1 << 3, # Bots and webhooks trigger user keywords
        "edit_trigger": 1 << 4, # Messages that get edited re-trigger
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

    MAX_KEYWORDS = 5

    def __init__(
                self,
                keywords: dict[int, set[Keyword]] = {0: set()},
                filters: dict[FilterEnum, set[Filter]] = {
                    FilterEnum.text_filter: set(),
                    FilterEnum.user_filter: set(),
                    FilterEnum.channel_filter: set(),
                    FilterEnum.server_filter: set()
                },
                settings: Settings = Settings.default(),
                mute_until: dt | None = None,
                opted_out: bool = False
            ) -> None:
        """Initializes a Stalker object"""
        self.keywords: dict[int, set[Keyword]] = keywords
        self.filters: dict[FilterEnum, set[Filter]] = filters
        self.settings: Settings = settings
        self.mute_until: dt | None = mute_until
        self.opted_out: bool = opted_out

    def clear(self):
        self.keywords = {0: set()}
        self.filters =  {
                    FilterEnum.text_filter: set(),
                    FilterEnum.user_filter: set(),
                    FilterEnum.channel_filter: set(),
                    FilterEnum.server_filter: set()
                }
        self.settings = Settings.default()
        self.mute_until = None
        self.opted_out = False

        return self

    def format_keywords(self, bot: client.Client) -> Embed:
        """Returns a formatted string listing a user's keywords"""

        add_command = bot.get_command("keyword add")
        command_mention = "`keyword add`"
        if add_command:
            command_mention = add_command.mention

        embed = Embed(title="Keywords", color=0xFEE75C)

        if not self.used_keywords:
            embed.description = ("You don't have any keywords! " +
                    f"Set some up by running the {command_mention} command.")
            return embed

        embed.description = (f"You are using " +
            f"{self.used_keywords}/{self.max_keywords} keywords")

        # Having a 0 key is guaranteed
        embed.add_field(
            name="__Global Keywords__",
            value = '- `' + '`\n- `'.join(map(str, sorted(self.keywords[0]))) + "`"
                    if self.keywords[0] else
                    ("You don't have any global keywords! " +
                    f"Set some up by running the {command_mention} command."),
            inline=False
        )

        server_specific_text = ""
        for server_id, keywords in self.keywords.items():
            # Skip the global keywords
            if not server_id:
                continue

            # If we can't find the guild in cache, let the user know
            server = get_guild_from_cache(bot, server_id)
            server_specific_text += (
                f"**{server.name}** ({server.id})" if server else
                f"**{server_id}** *(StalkerBot may not be in this server)*"
            ) + "\n"

            if keywords:
                server_specific_text += '- `' + '`\n- `'.join(
                    map(str, sorted(keywords))
                ) + "`\n"

        embed.add_field(
            name="__Server-Specific Keywords__",
            value = server_specific_text
                    if server_specific_text else
                    ("You don't have any server-specific keywords! " +
                    f"Set some up by running the {command_mention} command."),
            inline=False
        )
        return embed

    async def format_filters(
                self,
                bot: client.Client,
                guild_id: int | None = None
            ) -> Embed:
        """Returns a formatted embed listing a user's filters"""

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
                value= pre + sep.join(
                                [
                                    await f.get_list_identifier(guild_id, user_o)
                                    for f, user_o in filter_list
                            ]
                        ) if self.filters[filter_type] else
                        (f"*You don't have any {title.lower()}! " +
                        f"Set some up by running the {filter_mention} command.*"),
                inline=False
            )

        return embed

    @property
    def used_keywords(self) -> int:
        return sum([len(i) for i in self.keywords.values()])

    @property
    def max_keywords(self) -> int:
        return self.MAX_KEYWORDS

    def __repr__(self) -> str:
        return (f"Stalker("+
                f"keywords={self.keywords}, "
                f"filters={self.filters}, "
                f"settings={self.settings}, "
                f"mute_until={self.mute_until}, "
                f"opted_out={self.opted_out})"
            )

    def __str__(self) -> str:
        return self.__repr__()