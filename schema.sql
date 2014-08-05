drop table if exists entries;

create table entries(
	id integer primary key autoincrement,
	title text not null,
    time text not null,
    etime text not null,
    text text not null,
    score integer not null,
    username text not null,
    forum integer not null
);

create table staged(
	id integer primary key autoincrement,
	title text not null,
    time text not null,
    etime text not null,
    text text not null,
    score integer not null,
    username text not null,
    forum integer not null
);

create table deleted(
	id integer primary key autoincrement,
	title text not null,
    time text not null,
    etime text not null,
    text text not null,
    score integer not null,
    username text not null,
    forum integer not null
);
create table accounts(
    id integer primary key autoincrement,
	username text not null,
    password text not null,
    admin text not null,
    score integer not null
);
