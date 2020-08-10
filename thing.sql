create TABLE keywords(
    userID bigint,
    keyword text
);

create TABLE prefix(
    guildID bigint primary key,
    prefix VARCHAR(50)
);
