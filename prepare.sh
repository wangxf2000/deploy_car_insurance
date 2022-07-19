#! /bin/bash

echo "-- Commencing Car insurance cdsw model Setup Script"

set -e
set -u

echo "-- install dependency packages"
yum -y remove epel-release
yum install -y centos-release-scl epel-release
yum install -y rh-python36 python-pip
pip install --upgrade pip==19.3
pip install requests
BASE_DIR="/tmp/resource"

echo "--Download the models to ${BASE_DIR}"
##Download four models
if [ -d "${BASE_DIR}" ]; then
  mkdir -p ${BASE_DIR}
fi
git clone https://github.com/bguedes/carDetectionPredictionML
git clone https://github.com/bguedes/carDamagePredictionML
git clone https://github.com/bguedes/carDamageLocalizationPredictionML
git clone https://github.com/bguedes/carDamageSeverityPredictionML
cp carDetectionPredictionML/models/car_model_cat_list.pk  ${BASE_DIR}/car_model_cat_list.pk 
cp carDamagePredictionML/models/carDamagePredictionModel.h5   ${BASE_DIR}/carDamagePredictionModel.h5 
cp carDamageLocalizationPredictionML/models/carDamageLocalizationPredictionModel.h5  ${BASE_DIR}/carDamageLocalizationPredictionModel.h5
cp carDamageSeverityPredictionML/models/carDamageSeverityPredictionModel.h5  ${BASE_DIR}/carDamageSeverityPredictionModel.h5
#wget https://github.com/bguedes/carDetectionPredictionML/blob/main/models/car_model_cat_list.pk -P ${BASE_DIR}
#wget https://github.com/bguedes/carDamagePredictionML/blob/main/models/carDamagePredictionModel.h5  -P ${BASE_DIR}
#wget https://github.com/bguedes/carDamageLocalizationPredictionML/blob/main/models/carDamageLocalizationPredictionModel.h5 -P ${BASE_DIR}
#wget https://github.com/bguedes/carDamageSeverityPredictionML/blob/main/models/carDamageSeverityPredictionModel.h5 -P ${BASE_DIR}

echo "--Config THE_PWD env"
echo -n "supersecret1" > ${BASE_DIR}/the_pwd.txt
