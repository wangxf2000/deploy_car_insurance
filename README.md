# deploy_car_insurance

### deploy car insurance model and data
```
git clone https://github.com/wangxf2000/deploy_car_insurance.git
cd deploy_car_insurance
```

#### if your cdsw has already admin user, please use the following command to replace the password in the script. if not , please skip the the next step.
```
sed -i "s/supersecret1/YourPassword/" deploy_model.sh
```

#### deploy the model and data
```
sh prepare.sh
sh deploy_model.sh
sh deploy_data.sh
```
