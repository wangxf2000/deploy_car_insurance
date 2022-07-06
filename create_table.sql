CREATE external TABLE IF NOT EXISTS default.customers ( 
customer_id INT, 
car_plate_no STRING,
first_name STRING,
last_name STRING, 
city STRING, 
email STRING,
car_type STRING, 
PRIMARY KEY (customer_id,car_plate_no))
row format delimited fields terminated by ','
stored as TEXTFILE
location '/tmp/customers';

CREATE external TABLE IF NOT EXISTS default.claims ( 
claim_id INT, 
date_time timestamp,
severity STRING,
customer_id INT, 
car_plate_no STRING, 
PRIMARY KEY (claim_id))
row format delimited fields terminated by ','
stored as TEXTFILE
location '/tmp/claims';

create database IF NOT EXISTS car_insurance;

CREATE TABLE IF NOT EXISTS car_insurance.customers ( 
customer_id INT, 
car_plate_no STRING,
first_name STRING,
last_name STRING, 
city STRING, 
email STRING,
car_type STRING, 
PRIMARY KEY (customer_id,car_plate_no))
partition by hash partitions 4
stored as kudu;

CREATE TABLE IF NOT EXISTS car_insurance.claims ( 
claim_id BIGINT NOT NULL, 
time timestamp NOT NULL, 
severity STRING NOT NULL, 
customer_id BIGINT NOT NULL, 
car_plate_no STRING NOT NULL,
picture_path STRING NOT NULL,
PRIMARY KEY (claim_id))
partition by hash partitions 4
stored as kudu;

insert into car_insurance.customers
select customer_id,car_plate_no,first_name,last_name,city,email,car_type from default.customers;

insert into car_insurance.claims
select claim_id,date_time,severity,customer_id,car_plate_no,'' from default.claims;
