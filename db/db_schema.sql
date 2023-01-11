CREATE TABLE reservations (
    id int auto_increment not null,
    starttime datetime not null,
    endtime datetime not null,
    userid int not null,
    tableid int not null,
    capacity int not null,
    primary key (id),
    foreign key (userid) references users(id),
    foreign key (tableid) references table(id)
);

INSERT INTO reservations
VALUES (1, '2022-11-30 18:15:00', '2022-11-30 19:00:00', 1, 1, 3);

CREATE TABLE table (
    id int auto_increment not null,
    capacity int not null,
    primary key (id)
);

INSERT INTO table
VALUES (1, 7);

CREATE TABLE users (
    id int auto_increment not null,
    name varchar (50) not null,
    email varchar (50) not null,
    password varchar (256) not null,
    adminflag tinyint(1) not null,
    primary key (id)
);

INSERT INTO users
VALUES (1, 'maxmustermann', 'maxmustermann@gmail.com', 'passwort', 0)