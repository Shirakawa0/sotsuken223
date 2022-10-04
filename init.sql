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

CREATE TABLE schedule(
    id int,
    company VARCHAR(64) NOT NULL,
    date_time datetime NOT NULL,
    step VARCHAR(16) NOT NULL,
    detail VARCHAR(16) NOT NULL,
    place VARCHAR(16) NOT NULL,
    PRIMARY KEY(id,company,date_time)
);

CREATE TABLE practice(
    id int AUTO_INCREMENT PRIMARY KEY,
    student int NOT NULL,
    teacher VARCHAR(128) NOT NULL,
    date date NOT NULL,
    time VARCHAR(16) NOT NULL,
    check_flg BOOLEAN DEFAULT 0 NOT NULL
);

CREATE TABLE check(
    id int AUTO_INCREMENT PRIMARY KEY,
    student int NOT NULL,
    teacher VARCHAR(128) NOT NULL,
    title VARCHAR(32) NOT NULL,
    body VARCHAR(600) NOT NULL,
    check_flg BOOLEAN NOT NULL,
    propriety_flg BOOLEAN NOT NULL
)

CREATE TABLE class(
    id VARCHAR(4) PRIMARY KEY,
    dep_id VARCHAR(2),
    grade int,
    class int
);

