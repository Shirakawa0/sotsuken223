CREATE DATABASE sotsuken;
USE sotsuken;
CREATE TABLE u_account(
    id int PRIMARY KEY,
    hash_pw VARCHAR(128) NOT NULL,
    salt VARCHAR(5) NOT NULL,
    name VARCHAR(16) NOT NULL,
    class_id VARCHAR(4) NOT NULL
);