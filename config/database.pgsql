CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30)
);

create TABLE IF NOT EXISTS keywords(
    userID bigint,
    keyword text
);

create TABLE IF NOT EXISTS serverkeywords(
    userID bigint,
    serverid bigint,
    keyword text
);

create TABLE IF NOT EXISTS prefix(
    guildID bigint primary key,
    prefix VARCHAR(50)
);

create TABLE IF NOT EXISTS user_settings(
    userid bigint primary key,
    owntrigger boolean default true,
    quotetrigger boolean default true,
    embedmessage boolean default false,
    editmessage boolean default true,
    bottrigger boolean default true
);

create TABLE IF NOT EXISTS textfilters(
    userid bigint,
    textfilter text
);

create TABLE IF NOT EXISTS channelfilters(
    userid bigint,
    channelfilter BIGINT,
    PRIMARY KEY (userid, channelfilter)
);

create TABLE IF NOT EXISTS serverfilters(
    userid bigint,
    serverfilter BIGINT,
    PRIMARY KEY (userid, serverfilter)
);

create TABLE IF NOT EXISTS userfilters(
    userid bigint,
    userfilter BIGINT,
    PRIMARY KEY (userid, userfilter)
);

create TABLE IF NOT EXISTS tempmute(
    userid BIGINT PRIMARY KEY,
    time TIMESTAMP
);


CREATE TABLE IF NOT EXISTS role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, role_id, key)
);


CREATE TABLE IF NOT EXISTS channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, channel_id, key)
);
