from flask import Flask, render_template, request
from werkzeug.serving import run_simple

import re
import configparser
import os
import sys
sys.path.append('/home/pi/XTEC-PiPlayer') # Add path to import from directory
from mp2_details import config_path, version # pylint: disable=import-error

app = Flask(__name__)

# Homepage
@app.route('/', methods=['POST', 'GET'])
@app.route('/index.html', methods=['POST', 'GET'])
def index():
    # If user has pressed "Save"
    if request.method == 'POST':
        try:
            # Get the content and add to the ini file
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['devdesc'] = request.form['devdesc']
            ip = config['MP2']['ip']
            with open(config_path, 'w') as configfile:
                config.write(configfile)
        except Exception as ex:
            print('index.html: Error saving devdesc' + str(ex))
            return render_template('save_error.html', error="index.html: Error saving devdesc to ini: " + str(ex))
        
        return render_template('submit_ok.html', ip=ip)
    # Else load page
    else:
        # Grab the details from the ini file to show on the page
        dev_desc = '*error*'
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            dev_desc = config['MP2']['devdesc']
        except Exception as ex:
            print('index.html: Error getting info' + str(ex))
        return render_template('index.html', dev_desc=dev_desc, version=version)

# Network settings page
@app.route('/net.html', methods=['POST', 'GET'])
def net():
    # If user has pressed "Save"
    if request.method == 'POST':
        try:
            # Check entered info is acceptable
            ip = request.form['ip']
            if not is_valid_ipv4(ip):
                raise ValueError('Entered IP address of ' + ip + ' was incorrect')

            port = request.form['port']
            if not re.search(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$', port):
                raise ValueError('Entered Port number of ' + port + ' was incorrect')

            subnet = request.form['subnet']
            if not is_valid_ipv4(subnet):
                raise ValueError('Entered Subnet mask of ' + subnet + ' was incorrect')

            gateway = request.form['gateway']
            if not is_valid_ipv4(gateway):
                raise ValueError('Entered Gateway of ' + gateway + ' was incorrect')

            dns1 = request.form['dns1']
            if not is_valid_ipv4(dns1):
                raise ValueError('Entered DNS 1 of ' + dns1 + ' was incorrect')

            dns2 = request.form['dns2']
            if not is_valid_ipv4(dns2):
                raise ValueError('Entered DNS 2 of ' + dns2 + ' was incorrect')

        except Exception as ex:
            # A value was incorrectly entered
            return render_template('netdata_error.html', error=str(ex))
        
        # Values are okay. Save them to ini file
        try:
            # Get the content and add to the ini file
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['ip'] = ip
            config['MP2']['port'] = port
            config['MP2']['subnet'] = subnet
            config['MP2']['gateway'] = gateway
            config['MP2']['dns1'] = dns1
            config['MP2']['dns2'] = dns2

            with open(config_path, 'w') as configfile:
                config.write(configfile)
        except Exception as ex:
            return render_template('save_error.html', error="net.html: Error saving info to ini: " + str(ex))
        
        # Everything is hunky dory. Reboot the system
        # os.system("nohup sudo -b bash -c 'sleep 2; reboot' &>/dev/null;")
        return render_template('submit_ok.html', ip=ip)

    # Else load page
    else:
        ip = '*error*'
        port = '*error*'
        subnet = '*error*'
        gateway = '*error*'
        dns1 = '*error*'
        dns2 = '*error*'
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            ip = config['MP2']['ip']
            port = config['MP2']['port']
            subnet = config['MP2']['subnet']
            gateway = config['MP2']['gateway']
            dns1 = config['MP2']['dns1']
            dns2 = config['MP2']['dns2']
        except Exception as ex:
            print('net.html: Error getting info' + str(ex))
        return render_template('net.html', ip=ip, port=port, subnet=subnet, gateway=gateway, dns1=dns1, dns2=dns2)

# Digital inputs page
@app.route('/din.html', methods=['POST', 'GET'])
def din():
    # If user has pressed "Save"
    if request.method == 'POST':
        try:
            # Get the content and make sure it's kosher
            input1_on = request.form['input1_on']
            input1_off = request.form['input1_off']
            input2_on = request.form['input2_on']
            input2_off = request.form['input2_off']

            input1_on_track = request.form['input1_on_track']
            input1_off_track = request.form['input1_off_track']
            input2_on_track = request.form['input2_on_track']
            input2_off_track = request.form['input2_off_track']

            check_track_input(input1_on, input1_on_track, 'Input 1 On')
            check_track_input(input1_off, input1_off_track, 'Input 1 Off')
            check_track_input(input2_on, input2_on_track, 'Input 2 On')
            check_track_input(input2_off, input2_off_track, 'Input 2 Off')

            input1_on_ignore = request.form.get('input1_on_ignore', default='0')
            input1_off_ignore = request.form.get('input1_off_ignore', default='0')
            input2_on_ignore = request.form.get('input2_on_ignore', default='0')
            input2_off_ignore = request.form.get('input2_off_ignore', default='0')

        except Exception as ex:
            print('din.html: Error saving options' + str(ex))
            return render_template('save_error.html', error="din.html: Value error: " + str(ex))
        
        # Values are okay. Save to ini file
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['input1_on'] = input1_on
            config['MP2']['input1_off'] = input1_off
            config['MP2']['input2_on'] = input2_on
            config['MP2']['input2_off'] = input2_off
            
            config['MP2']['input1_on_track'] = input1_on_track
            config['MP2']['input1_off_track'] = input1_off_track
            config['MP2']['input2_on_track'] = input2_on_track
            config['MP2']['input2_off_track'] = input2_off_track

            config['MP2']['input1_on_ignore'] = input1_on_ignore
            config['MP2']['input1_off_ignore'] = input1_off_ignore
            config['MP2']['input2_on_ignore'] = input2_on_ignore
            config['MP2']['input2_off_ignore'] = input2_off_ignore
            
            ip = config['MP2']['ip']

            with open(config_path, 'w') as configfile:
                config.write(configfile)

        except Exception as ex:
            print('din.html: Error saving options' + str(ex))
            return render_template('save_error.html', error="din.html: Error saving options to ini: " + str(ex))

        return render_template('submit_ok.html', ip=ip)

    # Else load page
    else:
        input1_on = ''
        input1_off = ''
        input2_on = ''
        input2_off = ''
        input1_on_track = '0'
        input1_off_track = '0'
        input2_on_track = '0'
        input2_off_track = '0'
        input1_on_ignore = '0'
        input1_off_ignore = '0'
        input2_on_ignore = '0'
        input2_off_ignore = '0'

        try:
            # Get the content and add to the ini file
            config = configparser.ConfigParser()
            config.read(config_path)
            input1_on = config['MP2']['input1_on']
            input1_off = config['MP2']['input1_off']
            input2_on =  config['MP2']['input2_on']
            input2_off = config['MP2']['input2_off']

            input1_on_track = config['MP2']['input1_on_track']
            input1_off_track = config['MP2']['input1_off_track']
            input2_on_track =  config['MP2']['input2_on_track']
            input2_off_track = config['MP2']['input2_off_track']

            input1_on_ignore = config['MP2']['input1_on_ignore']
            input1_off_ignore = config['MP2']['input1_off_ignore']
            input2_on_ignore = config['MP2']['input2_on_ignore']
            input2_off_ignore = config['MP2']['input2_off_ignore']

        except Exception as ex:
            print('din.html: Error getting info' + str(ex))
        
        return render_template('din.html', input1_on=input1_on, input1_off=input1_off, input2_on=input2_on, input2_off=input2_off, \
            input1_on_track=input1_on_track, input1_off_track=input1_off_track, input2_on_track=input2_on_track, input2_off_track=input2_off_track, \
            input1_on_ignore=input1_on_ignore, input1_off_ignore=input1_off_ignore, input2_on_ignore=input2_on_ignore, input2_off_ignore=input2_off_ignore)

# Digital outputs page
@app.route('/dout.html')
def dout():
    return render_template('dout.html')

@app.route('/gen_error.html')
def gen_error():
    return render_template('gen_error.html')

@app.route('/netdata_error.html')
def netdata_error():
    return render_template('netdata_error.html')

# Others page
@app.route('/oth.html')
def oth():
    return render_template('oth.html')

# Save error page. Shown when there is an error saving data
@app.route('/save_error.html')
def save_error():
    return render_template('save_error.html')

# Submit successful page. Shown after successful save
@app.route('/submit_ok.html')
def submit_ok():
    return render_template('submit_ok.html')

############################################################################
# Helper functions
############################################################################
def is_valid_ipv4(ip):
    """A little regex to check if the ip is valid ipv4"""
    return re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip) 

def check_track_input(action, track_number, io):
    """ Checks track given for I/O input and makes sure its kosher """
    if action == "play" or action == "loop" or action == "random":
        if track_number == '':
            raise ValueError('Action ' + action + ' specified for ' + io + ' but no track number entered')

# def run_web_server(host):
#     """Runs the webserver"""
#     app.run(host=host, port=8080)
    
if __name__ == "__main__":
    """Runs the webserver"""
    app.run()
    # app.run(host='192.168.1.105',port=8080)