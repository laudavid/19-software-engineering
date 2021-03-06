import requests
import json
import uuid
import base64


def get_token():
    url = "https://openapi.baidu.com/oauth/2.0/token"
    grant_type = "client_credentials"
    api_key = "7OevAM3H1GUObzs9dbCZlnze"  # 自己申请的应用
    secret_key = "4CPUo8HGdIZ2CULYkEusYVTHGw8HVyG2"  # 自己申请的应用
    data = {'grant_type': 'client_credentials', 'client_id': api_key, 'client_secret': secret_key}
    r = requests.post(url, data=data)
    token = json.loads(r.text).get("access_token")
    return token


def recognize(sig, rate, token):
    url = "http://vop.baidu.com/server_api"
    speech_length = len(sig)
    speech = base64.b64encode(sig).decode("utf-8")
    mac_address = uuid.UUID(int=uuid.getnode()).hex[-12:]
    rate = rate
    data = {
        "format": "wav",
        "lan": "zh",
        "token": token,
        "len": speech_length,
        "rate": rate,
        "speech": speech,
        "cuid": mac_address,
        "channel": 1,
        "dev_pid":1537,
    }
    data_length = len(json.dumps(data).encode("utf-8"))
    headers = {"Content-Type": "application/json",
               "Content-Length": str(data_length)}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    print(r.text)


filename = "16k.wav"

signal = open(filename, "rb").read()
rate = 8000

token = get_token()
recognize(signal, rate, token)