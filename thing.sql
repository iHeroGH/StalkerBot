create TABLE keywords(
    userID bigint,
    keyword text
);

create TABLE prefix(
    guildID bigint primary key,
    prefix VARCHAR(50)
);

create TABLE usersettings(
    userid bigint primary key,
    owntrigger boolean,
    quotetrigger boolean
);
