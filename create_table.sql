create database IF NOT EXISTS car_insurance;


CREATE TABLE IF NOT EXISTS car_insurance.claims ( 
claimId STRING NOT NULL,
carImageBased64encoding  STRING NOT NULL,
clainDate timestamp NOT NULL, 
customerId STRING NOT NULL,
latitude double  NOT NULL,
longitude double  NOT NULL,
carDetected STRING NOT NULL, 
severity STRING NOT NULL, 
localization STRING NOT NULL,
isDamaged STRING NOT NULL,
PRIMARY KEY (claimId))
partition by hash partitions 4
stored as kudu;
