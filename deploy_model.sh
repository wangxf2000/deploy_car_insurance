#! /bin/bash

echo "-- Commencing Car insurance cdsw model Setup Script"

set -e
set -u

echo "-- install dependency packages"
yum install -y centos-release-scl
yum install -y rh-python36 
pip install requests
BASE_DIR="/tmp/resource"

echo "--Download the models to ${BASE_DIR}"
##Download four models
if [ -d "${BASE_DIR}" ]; then
  mkdir -p ${BASE_DIR}
fi
wget https://github.com/bguedes/carDetectionPredictionML/blob/main/models/car_model_cat_list.pk -P ${BASE_DIR} 
wget https://github.com/bguedes/carDamagePredictionML/blob/main/models/carDamagePredictionModel.h5  -P ${BASE_DIR}
wget https://github.com/bguedes/carDamageLocalizationPredictionML/blob/main/models/carDamageLocalizationPredictionModel.h5 -P ${BASE_DIR}
wget https://github.com/bguedes/carDamageSeverityPredictionML/blob/main/models/carDamageSeverityPredictionModel.h5 -P ${BASE_DIR}

echo "--Config THE_PWD env"
echo -n "supersecret1" > ${BASE_DIR}/the_pwd.txt

echo "--get hostname ip"
PUBLIC_IP=$(curl -s http://ifconfig.me || curl -s http://api.ipify.org/)


source /opt/rh/rh-python36/enable

echo "--deploy the cdsw project and models"
echo "--deploy carPictureDetection_cdsw_setup..."
python -u setup_model/carPictureDetection_cdsw_setup.py $PUBLIC_IP ${BASE_DIR}/car_model_cat_list.pk  ${BASE_DIR}/the_pwd.txt
echo "--deploy carPictureDetection_cdsw_setup completely"
echo "--deploy carDamagePrediction_cdsw_setup..."
python -u setup_model/carDamagePrediction_cdsw_setup.py $PUBLIC_IP ${BASE_DIR}/carDamagePredictionModel.h5  ${BASE_DIR}/the_pwd.txt
echo "--deploy carDamagePrediction_cdsw_setup completely"
echo "--deploy carDamageLocalization_cdsw_setup..."
python -u setup_model/carDamageLocalization_cdsw_setup.py $PUBLIC_IP ${BASE_DIR}/carDamageLocalizationPredictionModel.h5  ${BASE_DIR}/the_pwd.txt
echo "--deploy carDamageLocalization_cdsw_setup completely"
echo "--deploy carDamageSeverity_cdsw_setup..."
python -u setup_model/carDamageSeverity_cdsw_setup.py $PUBLIC_IP ${BASE_DIR}/carDamageSeverityPredictionModel.h5  ${BASE_DIR}/the_pwd.txt
echo "--deploy carDamageSeverity_cdsw_setup completely"
echo "--Deploy all cdsw models completely"

