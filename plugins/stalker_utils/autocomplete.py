import novus as n
from novus import types as t
from novus.ext.client import Client

from .misc_utils import get_users_from_cache
from .stalker_cache_utils import get_stalker
from .stalker_objects import Filter, FilterEnum, Keyword

SHOW_OPTIONS = 25

def predictive_choices(
            choices: list[n.ApplicationCommandChoice],
            entered: str
        ) -> list[n.ApplicationCommandChoice]:
    """
    Dynamically removes autocomplete options that don't contain with
    what the user entered. Also removes duplicates. If no options are found
    that match what the user entered, the entire list is returned.
    """
    entered = entered.lower()

    fixed_choices = []
    encountered_choices: set[str] = set()
    for choice in choices:
        if entered in choice.name.lower() and choice.name not in encountered_choices:
            fixed_choices.append(choice)
            encountered_choices.add(choice.name)

    if not fixed_choices:
        return choices

    return fixed_choices

async def current_guild_autocomplete(
            bot: Client,
            ctx: t.CommandI
        ) -> list[n.ApplicationCommandChoice]:
    """Retrieves an option for the current guild"""
    Filter.bot = bot

    if not ctx.guild:
        return []

    fake_filter = Filter(ctx.guild.id, FilterEnum.server_filter)
    choices = [
        n.ApplicationCommandChoice(
            name=await fake_filter.get_list_identifier(md="", mention=False),
            value=str(ctx.guild.id)
        )
    ]

    return choices

async def available_guilds_autocomplete(
            bot: Client,
            ctx: t.CommandI,
            options: dict[str, n.InteractionOption] | None = None
        ) -> list[n.ApplicationCommandChoice]:
    """Retrieves an option for the guilds the user has keywords in"""
    Filter.bot = bot

    if not ctx.guild:
        return []

    stalker = get_stalker(ctx.user.id)

    choices = [
        n.ApplicationCommandChoice(name="Global", value="0")
    ] if stalker.keywords[0] else []

    for guild_id in stalker.keywords:
        if not guild_id:
            continue

        fake_filter = Filter(guild_id, FilterEnum.server_filter)
        choices.append(
            n.ApplicationCommandChoice(
                name=await fake_filter.get_list_identifier(md="", mention=False),
                value=str(guild_id)
            )
        )

    entered = ""
    if options and "server_id" in options:
        entered = str(options["server_id"].value)

    return predictive_choices(choices, entered)[:SHOW_OPTIONS]

async def filter_autocomplete(
            ctx: t.CommandI,
            filter_type: FilterEnum,
            options: dict[str, n.InteractionOption] | None = None,
            bot: Client | None = None
        ) -> list[n.ApplicationCommandChoice]:
    """Retrieves the autocomplete options for a given filter type"""

    stalker = get_stalker(ctx.user.id)

    guild_id = None
    if ctx.guild:
        guild_id = ctx.guild.id

    if filter_type == FilterEnum.user_filter:
        users = await get_users_from_cache(
            bot,
            [filter.filter for filter in stalker.filters[FilterEnum.user_filter]],
            guild_id
        )

        choices = [
            n.ApplicationCommandChoice(
                name=user.username if isinstance(user, n.GuildMember) else str(user),
                value=str(user.id) if isinstance(user, n.GuildMember) else str(user)
            )
            for user in sorted(
                users,
                key=lambda x: x.username if isinstance(x, n.GuildMember) else str(x)
            )
        ]
    else:
        choices = [
            n.ApplicationCommandChoice(
                name=await filter.get_list_identifier(
                        guild_id, md="", mention=False
                    ),
                value=str(filter.filter)
            )
            for filter in sorted(stalker.filters[filter_type])
        ]

    entered: str = ""
    if options:
        entered = str(options["filter"].value)

    return predictive_choices(choices, entered)[:SHOW_OPTIONS]

async def keyword_autocomplete(
            bot: Client,
            ctx: t.CommandI,
            options: dict[str, n.InteractionOption] | None = None,
        ) -> list[n.ApplicationCommandChoice]:
    """Retrieves the autocomplete options of the user's keywords"""

    stalker = get_stalker(ctx.user.id)

    # If it's 0: we only display global keywords
    # If it's a server ID: we only display that server's keywords
    chosen_guild: int = 0
    if options and "server_id" in options:
        entered = options["server_id"].value

        if isinstance(entered, str) and entered.isdigit():
            entered = int(entered)

        if isinstance(entered, int) and not isinstance(entered, bool):
            chosen_guild = entered

    visible_keywords = [keyword for keyword in stalker.keywords[chosen_guild]]

    choices = [
        n.ApplicationCommandChoice(
            name=str(keyword)
        )
        for keyword in sorted(visible_keywords)
    ]

    entered_keyword = ""
    if options and "keyword" in options:
        entered_keyword = str(options["keyword"].value)

    return predictive_choices(choices, entered_keyword)[:SHOW_OPTIONS]

FILTER_TYPE_OPTIONS: list[n.ApplicationCommandChoice] = [
    n.ApplicationCommandChoice(
        name="Text",
        value="t"
    ),
    n.ApplicationCommandChoice(
        name="User",
        value="u"
    ),
    n.ApplicationCommandChoice(
        name="Channel",
        value="c"
    ),
    n.ApplicationCommandChoice(
        name="Server",
        value="s"
    ),
    n.ApplicationCommandChoice(
        name="All",
        value="*"
    )
]

KEYWORD_TYPE_OPTIONS: list[n.ApplicationCommandChoice] = [
    n.ApplicationCommandChoice(
        name="Global",
        value="g"
    ),
    n.ApplicationCommandChoice(
        name="Server-Specific",
        value="s"
    ),
    n.ApplicationCommandChoice(
        name="Both",
        value="*"
    )
]

SETTING_OPTIONS: list[n.ApplicationCommandChoice] = [
    n.ApplicationCommandChoice(
        name="Trigger your own keywords",
        value="self_trigger"
    ),
    n.ApplicationCommandChoice(
        name="Keywords in >quotes are triggered",
        value="quote_trigger"
    ),
    n.ApplicationCommandChoice(
        name="Replies send a DM",
        value="reply_trigger"
    ),
    n.ApplicationCommandChoice(
        name="Bots trigger keywords",
        value="bot_trigger"
    ),
    n.ApplicationCommandChoice(
        name="Edits trigger keywords",
        value="edit_trigger"
    ),
    n.ApplicationCommandChoice(
        name="DMs are embedded",
        value="embed_messages"
    )
]