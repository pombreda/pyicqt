# Introduction #

If you run into performance issues with a MySQL database, try using this fixed version of the db-setup.mysql script by RipZ:


# db-setup.mysql #

--
-- This is the required schema for MySQL. Load this into the database
-- using the mysql interactive terminal:
--
--     mysql> \. db-setup.mysql
--
-- Then make sure you create a user in MySQL and grant it full access
-- to the pyicqt database.  You will need to enter this information
-- into your PyICQt config file.
--

CREATE DATABASE pyicqt;
USE pyicqt;

--
-- registration table
--
CREATE TABLE `register` (
> `owner` varchar(256) NOT NULL,
> `username` TINYTEXT,
> `password` TINYTEXT,
> `encryptedpassword` TINYTEXT,
> UNIQUE KEY `owner` (`owner`)
);

--
-- settings table
--
CREATE TABLE `settings` (
> `owner` varchar(256) NOT NULL,
> `variable` TINYTEXT,
> `value` TINYTEXT
);

--
-- lists table
--
CREATE TABLE `lists` (
> `owner` varchar(256) NOT NULL,
> `type` TINYTEXT NOT NULL,
> `jid` TINYTEXT,
> KEY `lists` (`owner`)
);

--
-- list attributes table
--
CREATE TABLE `list_attributes` (
> `owner` varchar(256) NOT NULL,
> `type` TINYTEXT NOT NULL,
> `jid` TINYTEXT,
> `attribute` TINYTEXT,
> `value` TINYTEXT,
> KEY `list_attributes` (`owner`)
);

--
-- custom settings table
--
CREATE TABLE `csettings` (
> `owner` varchar(256) NOT NULL,
> `variable` TINYTEXT,
> `value` TINYTEXT,
> KEY `csettings` (`owner`)
);

--
-- x-statuses table
--
CREATE TABLE `xstatuses` (
> `owner` varchar(256) NOT NULL,
> `number` TINYTEXT,
> `title` TINYTEXT,
> `value` TINYTEXT,
> KEY `xstatuses` (`owner`)
);