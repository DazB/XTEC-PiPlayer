from flask import Flask, render_template, request
from werkzeug.serving import run_simple

import configparser

version = '0.1'

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
@app.route('/index.html', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            config['MP2']['DevDesc'] = request.form['DevDesc']
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as ex:
            return render_template('save_error.html', error="index.html: Error saving DevDesc to ini:" + str(ex))
        
        return render_template('submit_ok.html')
    else:
        dev_desc = ''
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            dev_desc = config['MP2']['DevDesc']
        except Exception as ex:
            dev_desc = 'Error getting descirption'
        return render_template('index.html', dev_desc=dev_desc, version=version)

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


# def run_web_server(host):
#     """Runs the webserver"""
#     app.run(host=host, port=8080, debug=True)
    
if __name__ == "__main__":
    """Runs the webserver"""
    app.run()