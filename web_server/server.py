from flask import Flask, render_template
from werkzeug.serving import run_simple

app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/din.html')
def din():
    return render_template('din.html')

@app.route('/dout.html')
def dout():
    return render_template('dout.html')

@app.route('/gen_error.html')
def gen_error():
    return render_template('gen_error.html')

@app.route('/net.html')
def net():
    return render_template('net.html')

@app.route('/netdata_error.html')
def netdata_error():
    return render_template('netdata_error.html')

@app.route('/oth.html')
def oth():
    return render_template('oth.html')

@app.route('/save_error.html')
def save_error():
    return render_template('save_error.html')

@app.route('/submit_ok.html')
def submit_ok():
    return render_template('submit_ok.html')

def run_web_server(host):
    """Runs the webserver"""
    app.run(host=host, port=8080)
    