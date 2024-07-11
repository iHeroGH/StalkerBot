-- The stalker_channels table keeps track of created DM channel IDs
CREATE TABLE IF NOT EXISTS stalker_channels(
    user_id BIGINT PRIMARY KEY NOT NULL,
    channel_id BIGINT NOT NULL
);

-- The user_settings table keeps track of various adjustable settings
CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY NOT NULL,
    self_trigger BOOLEAN default False,
    quote_trigger BOOLEAN default True,
    reply_trigger BOOLEAN default True,
    bot_trigger BOOLEAN default False,
    edit_trigger BOOLEAN default True,
    embed_message BOOLEAN default True
);

-- The keywords table keeps track of all users and their keywords
CREATE TABLE IF NOT EXISTS keywords(
    user_id BIGINT NOT NULL,
    keyword TEXT NOT NULL,

    PRIMARY KEY (user_id, keyword)
);

-- Server-Specific keywords
CREATE TABLE IF NOT EXISTS server_keywords(
    user_id BIGINT NOT NULL,
    keyword TEXT NOT NULL,
    server_id BIGINT NOT NULL,

    PRIMARY KEY (user_id, keyword, server_id)
);

-- Channel-Specific keywords
CREATE TABLE IF NOT EXISTS channel_keywords(
    user_id BIGINT NOT NULL,
    keyword TEXT NOT NULL,
    channel_id BIGINT NOT NULL,

    PRIMARY KEY (user_id, keyword, channel_id)
);

-- Special keywords
CREATE TABLE IF NOT EXISTS special_keywords(
    user_id BIGINT NOT NULL,
    whitelist keyword_type[],
    blacklist keyword_type[]
)
CREATE TYPE keyword_type(
    keyword TEXT,
    is_exact BOOLEAN
)


-- Filters all follow the general format of the user_id and the filter
CREATE TABLE IF NOT EXISTS text_filters(
    user_id BIGINT NOT NULL,
    filter TEXT NOT NULL,

    PRIMARY KEY (user_id, filter)
);

CREATE TABLE IF NOT EXISTS user_filters(
    user_id BIGINT NOT NULL,
    filter BIGINT NOT NULL,

    PRIMARY KEY (user_id, filter)
);

CREATE TABLE IF NOT EXISTS channel_filters(
    user_id BIGINT NOT NULL,
    filter BIGINT NOT NULL,

    PRIMARY KEY (user_id, filter)
);

CREATE TABLE IF NOT EXISTS server_filters(
    user_id BIGINT NOT NULL,
    filter BIGINT NOT NULL,

    PRIMARY KEY (user_id, filter)
);

-- The temp_mute table keeps track of users who have muted the bot until
-- a certain timestamp
CREATE TABLE IF NOT EXISTS temp_mute(
    user_id BIGINT PRIMARY KEY NOT NULL,
    unmute_at TIMESTAMP
);

-- The user_opt_out table keeps track of users who have opted out
-- of the bot's features (their messages will not be sent to others, and other
-- people's messages will not get sent to them)
CREATE TABLE IF NOT EXISTS user_opt_out(
    user_id BIGINT PRIMARY KEY NOT NULL
);