from flask import Flask, render_template, request

import requests
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
API_KEY = "7FGNzBcGOMBIR-LTevrXYzj50iLFF2lJw2jYIkuus7wn"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}

app = Flask(__name__)# interface between my server and my application wsgi


@app.route('/')#binds to an url
def index():
    return render_template('home.html')

@app.route('/predict') 
def predict():
    return render_template('predict.html')
@app.route('/y_predict', methods= ['POST']) 
def y_predict():
    regyear = int(request.form['Registrationyear'])
    powerps = int(request.form['PowerofcarinPS'])
    kms =int(request.form['KilometersDriven'])
    regmonth =int(request.form.get('Registrationmonth'))
    gearbox =(request.form['Geartype'])
    damage =request.form['cd']
    model = request.form.get('model')
    brand =request.form.get('brand') 
    fuelType =request.form.get('fueltype') 
    vehicletype = request.form.get('vechicletype')
    row = {'vehicleType': vehicletype,'yearOfRegistration':regyear, 
           'gearbox': gearbox,'powerPS': powerps, 'model':model,'kilometer': kms, 
           'monthOfRegistration': regmonth,'fuelType': fuelType,
           'brand': brand,'notRepairedDamage': damage}
    print(row)
    new_row = pd.DataFrame([row])
    new_df = pd.DataFrame(columns = ['vehicleType', 'yearOfRegistration', 'gearbox',
                           'powerPS','model', 'kilometer', 'monthOfRegistration', 'fuelType',
                           'brand','notRepairedDamage' ])
    new_df=pd.concat([new_df,new_row], ignore_index = True)
    new_df['monthOfRegistration']= new_df['monthOfRegistration'].astype(int)
    labels = ['gearbox', 'notRepairedDamage', 'model', 'brand', 'fuelType', 'vehicleType'] 
    mapper = {}
    for i in labels:
        mapper[i] = LabelEncoder()
        mapper[i].fit(new_df[i]) 
        mapper[i].classes_ = np.load(str('classes'+i+'.npy'),allow_pickle=True) 
        tr = mapper[i].fit_transform(new_df[i])
        new_df.loc[:, i + '_labels'] = pd.Series (tr, index=new_df.index)
    labeled = new_df[ ['yearOfRegistration', 'powerPS','kilometer','monthOfRegistration']
        + [x+'_labels' for x in labels]]
    X = labeled.values
    X= X.tolist()
    print(X)
    
  
    payload_scoring = {"input_data": [{"field": ['f0', 'f1', 'f2',
                           'f3','f4', 'f5', 'f6', 'f7',
                           'f8','f9' ], 
                                      "values":X }]}
    #payload_scoring = {"input_data": [{"fields": [array_of_input_fields], "values": [array_of_values_to_be_scored, another_array_of_values_to_be_scored]}]}
    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/2e6b4079-fdd3-4b9b-8427-f309d0af6b20/predictions?version=2022-11-16', json=payload_scoring,
    headers={'Authorization': 'Bearer ' + mltoken})
    print("Scoring response")
    
    
    predictions=response_scoring.json()
    df_ev = np.exp(predictions['predictions'][0]['values'][0][0])
    print(df_ev)
        
    return render_template('predict.html',y = 'The resale value predicted is {:.2f}$'.format(df_ev))

if __name__=='__main__':
    app.run(debug= False)
    
