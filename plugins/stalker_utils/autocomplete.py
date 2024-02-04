import novus as n
from novus import types as t
from novus.ext.client import Client

from .misc_utils import get_users_from_cache
from .stalker_cache_utils import get_stalker
from .stalker_objects import Filter, FilterEnum

SHOW_OPTIONS = 25

def predictive_choices(
            choices: list[n.ApplicationCommandChoice],
            entered: str
        ) -> list[n.ApplicationCommandChoice]:
    """
    Dynamically removes autocomplete options that don't start with
    what the user entered
    """
    return [choice for choice in choices if choice.name.startswith(entered)]

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

async def filter_type_options() -> list[n.ApplicationCommandChoice]:
        """Returns choices for clearing all filters depending on type"""

        choices = [
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

        return choices

async def keyword_type_options() -> list[n.ApplicationCommandChoice]:
        """Returns choices for clearing all keywords depending on type"""

        choices = [
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

        return choices