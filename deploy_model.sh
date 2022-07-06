#! /bin/bash

echo "-- Commencing Car insurance cdsw model Setup Script"

set -e
set -u

echo "-- install dependency packages"
yum install -y centos-release-scl
yum install -y rh-python36 
pip install requests

echo "--Download the models to /tmp/resources"
##Download four models
mkdir /tmp/resources
wget https://github.com/bguedes/carDetectionPredictionML/blob/main/models/car_model_cat_list.pk -P /tmp/resources 
wget https://github.com/bguedes/carDamagePredictionML/blob/main/models/carDamagePredictionModel.h5  -P /tmp/resources
wget https://github.com/bguedes/carDamageLocalizationPredictionML/blob/main/models/carDamageLocalizationPredictionModel.h5 -P /tmp/resources
wget https://github.com/bguedes/carDamageSeverityPredictionML/blob/main/models/carDamageSeverityPredictionModel.h5 -P /tmp/resources

echo "--Config THE_PWD env"
export THE_PWD=admin

echo "--get hostname ip"

export PUBLIC_IP=$(curl -s http://ifconfig.me || curl -s http://api.ipify.org/)


source /opt/rh/rh-python36/enable

export THE_PWD=admin
echo "--deploy the cdsw project and models"
echo "--deploy carPictureDetection_cdsw_setup..."
python -u setup_model/carPictureDetection_cdsw_setup.py $PUBLIC_IP /tmp/resources/car_model_cat_list.pk
echo "--deploy carPictureDetection_cdsw_setup completely"
echo "--deploy carDamagePrediction_cdsw_setup..."
python -u setup_model/carDamagePrediction_cdsw_setup.py $PUBLIC_IP /tmp/resources/carDamagePredictionModel.h5
echo "--deploy carDamagePrediction_cdsw_setup completely"
echo "--deploy carDamageLocalization_cdsw_setup..."
python -u setup_model/carDamageLocalization_cdsw_setup.py $PUBLIC_IP /tmp/resources/carDamageLocalizationPredictionModel.h5
echo "--deploy carDamageLocalization_cdsw_setup completely"
echo "--deploy carDamageSeverity_cdsw_setup..."
python -u setup_model/carDamageSeverity_cdsw_setup.py $PUBLIC_IP /tmp/resources/carDamageSeverityPredictionModel.h5
echo "--deploy carDamageSeverity_cdsw_setup completely"
echo "--Deploy all cdsw models completely"

