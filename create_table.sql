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
claimId BIGINT NOT NULL,
carImageBased64encoding  STRING NOT NULL,
clainDate timestamp NOT NULL, 
isDamaged STRING NOT NULL, 
localization STRING NOT NULL, 
severity STRING NOT NULL,
PRIMARY KEY (claimId))
partition by hash partitions 4
stored as kudu;

insert into car_insurance.customers
select customer_id,car_plate_no,first_name,last_name,city,email,car_type from default.customers;

