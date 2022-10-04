CREATE DATABASE sotsuken;
USE sotsuken;
CREATE TABLE u_account(
    id int PRIMARY KEY,
    hash_pw VARCHAR(128) NOT NULL,
    salt VARCHAR(5) NOT NULL,
    name VARCHAR(16) NOT NULL,
    class_id VARCHAR(4) NOT NULL
);

CREATE TABLE teacher_class(
    id varchar(64) PRIMARY KEY NOT NULL,
    class_id VARCHAR(4) PRIMARY KEY NOT NULL
);

CREATE TABLE a_account(
    id VARCHAR(64) PRIMARY KEY NOT NULL,
    hash_pw VARCHAR(128) NOT NULL,
    salt VARCHAR(5) NOT NULL,
    name VARCHAR(16) NOT NULL,
    public_flg BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE comments(
    id int NOT NULL auto_increment PRIMARY KEY,
    thread_id int NOT NULL PRIMARY KEY,
    body VARCHAR(500) NOT NULL
);

CREATE TABLE threads(
    id int NOT NULL auto_increment PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

