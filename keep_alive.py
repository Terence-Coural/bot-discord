from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/online/')
def home():
    return "La secrétaire est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()