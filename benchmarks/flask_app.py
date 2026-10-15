from flask import Flask


app = Flask(__name__)


@app.get('/')
def hello():
    return 'Your Pyjo is working!'
