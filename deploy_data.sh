#! /bin/bash

echo "-- Commencing Car insurance data Setup Script"

set -e
set -u

echo "-- deploy mock data in HDFS"
export HADOOP_USER_NAME=hdfs
hdfs dfs -mkdir -p /tmp/customers
hdfs dfs -mkdir -p /tmp/claims
hdfs dfs -chown -R impala:hadoop /tmp/customers
hdfs dfs -chown -R impala:hadoop /tmp/claims
export HADOOP_USER_NAME=impala
hdfs dfs -put customers.csv /tmp/customers
hdfs dfs -put claims.csv /tmp/claims

echo "-- Create kudu tables and initial data"
impala-shell -f ~/car_insurance/create_table.sql -B -o ~/car_insurance/create_table.sql.log

echo "-- Create kudu tables and initial data completely"

