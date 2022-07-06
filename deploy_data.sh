#! /bin/bash

echo "-- Commencing SingleNodeCluster Setup Script"

set -e
set -u

export HADOOP_USER_NAME=hdfs
hdfs dfs -mkdir -p /tmp/customers
hdfs dfs -mkdir -p /tmp/claims
hdfs dfs -chown -R impala:hadoop /tmp/customers
hdfs dfs -chown -R impala:hadoop /tmp/claims
export HADOOP_USER_NAME=impala
hdfs dfs -put ~/car_insurance/customers.csv /tmp/customers
hdfs dfs -put ~/car_insurance/claims.csv /tmp/claims

impala-shell -f ~/car_insurance/create_table.sql -B -o ~/car_insurance/create_table.sql.log
