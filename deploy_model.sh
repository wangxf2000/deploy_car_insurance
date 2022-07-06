git clone https://github.com/bguedes/carDetectionPredictionML
git clone https://github.com/bguedes/carDamagePredictionML
git clone https://github.com/bguedes/carDamageLocalizationPredictionML
git clone https://github.com/bguedes/carDamageSeverityPredictionML



yum install -y centos-release-scl
yum install -y rh-python36 
pip install requests


source /opt/rh/rh-python36/enable

export THE_PWD=admin
nohup python -u /root/car_insurance/cdsw_setup.py 10.0.211.135 /root/carDetectionPredictionML/models/car_model_cat_list.pk &



cat > .pip/pip.conf <<EOF
##Note, this file is written by cloud-init on first boot of an instance
## modifications made here will not survive a re-bundle.
###
[global]
index-url=http://mirrors.cloud.aliyuncs.com/pypi/simple/

[install]
trusted-host=mirrors.cloud.aliyuncs.com
EOF
