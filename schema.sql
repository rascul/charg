drop table if exists users cascade;
create table users (
  uid serial primary key,
  email text not null unique
);

drop table if exists chars cascade;
create table chars (
  charid serial primary key,
  creator serial references users(uid),
  created timestamp default current_timestamp,
  released timestamp,
  expires timestamp,
  name text,
  password text,
  owner text,
  moves int,
  hitpoints int,
  level int,
  race text,
  char_class text,
  homeland text,
  stat_str int,
  stat_int int,
  stat_wil int,
  stat_dex int,
  stat_con int,
  notes text,
  rent text,
  sex text
);

drop table if exists requests cascade;
create table requests (
  requestid serial primary key,
  charid serial not null references chars(charid),
  name text not null,
  email text not null,
  stamp timestamp
);
