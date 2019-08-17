from flask import Flask, render_template, request, json, jsonify
import os
import math
from wiotp import sdk
import json
import numpy as np
import io
from watson_machine_learning_client import WatsonMachineLearningAPIClient
from PIL import Image

app = Flask(__name__)
app.config.from_object(__name__)
port = int(os.getenv('PORT', 8080))
response_iot = None
resposta = None

@app.route("/", methods=['GET'])
def hello():
    error=None
    return render_template('index.html', error=error)

def myStatusCallback(status):
    global response_iot
    response_iot = status.data
    print('response', response_iot)
#test
myConfig = { 
    "auth": {
        "key": "a-y76ylb-ckj29x2v6b",
        "token": "IoZc5eC_lxrtJdmi4O"
    }
}
client = sdk.application.ApplicationClient(config=myConfig)
client.connect()
client.subscribeToDeviceEvents(typeId='maratona', deviceId='d9', eventId='sensor')
client.deviceEventCallback = myStatusCallback
client.subscribeToDeviceEvents()


@app.route("/iot", methods=['GET'])
def result():
    print(request.args)
    data = response_iot['data']
    umidade_ar = response_iot['data']['umidade_ar']
    temperatura = response_iot['data']['temperatura']
    umidade_solo = response_iot['data']['umidade_solo']
    itu = temperatura - 0.55 * ( 1 - umidade_ar ) * ( temperatura - 14 )
    resposta = {
        "iotData": data,
        "itu": itu,
        "volumeAgua": umidade_solo * 4 * math.pi / 6,
        "fahrenheit": temperatura * 9 / 5 + 32
    }
    
    # Implemente sua lógica aqui e insira as respostas na variável 'resposta'

    response = app.response_class(
        response=json.dumps(resposta),
        status=200,
        mimetype='application/json'
    )
    return response

def prepare_image(image):
    image = image.resize(size=(96,96))
    image = np.array(image, dtype="float") / 255.0
    image = np.expand_dims(image,axis=0)
    image = image.tolist()
    return image

@app.route('/predict', methods=['POST'])
def predict():
    print(request)
    image = request.files["image"].read()
    image = Image.open(io.BytesIO(image))
    image = prepare_image(image)

    # Faça uma requisição para o serviço Watson Machine Learning aqui e retorne a classe detectada na variável 'resposta'
    wml_credentials  = {
        "apikey": "w0Jfv25Y1emvcA6aA-Gf_Eys9ZzPpHj0EQdASS3Kbldz",
        "iam_apikey_description": "Auto-generated for key b1e50421-929e-4d18-98e9-32729c898390",
        "iam_apikey_name": "wdp-writer",
        "iam_role_crn": "crn:v1:bluemix:public:iam::::serviceRole:Writer",
        "iam_serviceid_crn": "crn:v1:bluemix:public:iam-identity::a/c803aecf7aac4d009194a0cce5abb600::serviceid:ServiceId-7cdc734b-12d3-4b8c-90fd-8ac4d377d601",
        "instance_id": "bdd4074e-e090-4d18-998d-c2cf18a1f3e6",
        "url": "https://us-south.ml.cloud.ibm.com"
    }
    client = WatsonMachineLearningAPIClient( wml_credentials )
    model_payload = { "values" : image }
    ai_parms = { "wml_credentials" : wml_credentials, "model_endpoint_url" : 'https://us-south.ml.cloud.ibm.com/v3/wml_instances/bdd4074e-e090-4d18-998d-c2cf18a1f3e6/deployments/8165db11-40d7-438b-ac99-714156339e5f/online' }
    model_result = client.deployments.score( ai_parms["model_endpoint_url"], model_payload )


    resposta = {
        "class": "praga" if model_result['values'][0][1][0] == 1 else "normal"
    }
    return resposta

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)