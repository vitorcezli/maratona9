from flask import Flask, render_template, request, json, jsonify
import os
from wiotp import sdk
import json
import numpy as np
import io
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
        "volumeAgua": umidade_solo * 4.19,
        "fahrenheit": (32 * temperatura - 32) * 5 / 9
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
    
    resposta = {
        "class": "data"
    }
    return resposta

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)