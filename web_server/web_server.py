from flask import Flask, render_template, request
from werkzeug.serving import run_simple

import re
import configparser
import os
import sys
import threading
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
            config['MP2']['audio'] = request.form['audio']
            ip = config['MP2']['ip']

            with open(config_path, 'w') as configfile:
                config.write(configfile)
        except Exception as ex:
            print('index.html: Error saving devdesc: ' + str(ex))
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
            audio = config['MP2']['audio']
        except Exception as ex:
            print('index.html: Error getting info: ' + str(ex))
        return render_template('index.html', dev_desc=dev_desc, version=version, audio=audio)

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

            tcp_port = request.form['tcp_port']
            if not re.search(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$', tcp_port):
                raise ValueError('Entered TCP Port number of ' + tcp_port + ' was incorrect')
            elif tcp_port == '80':
                raise ValueError('TCP Port number of ' + tcp_port + ' not allowed')

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

            ftp_user = request.form['ftp_user']
            ftp_password = request.form['ftp_password']
            ftp_port = request.form['ftp_port']
            if not re.search(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$', ftp_port):
                raise ValueError('Entered FTP Port number of ' + ftp_port + ' was incorrect')
            elif ftp_port == '80':
                raise ValueError('FTP Port number of ' + ftp_port + ' not allowed')
            elif ftp_port == tcp_port:
                raise ValueError('FTP Port and TCP Port must be different')


        except Exception as ex:
            # A value was incorrectly entered
            return render_template('netdata_error.html', error=str(ex))
        
        # Values are okay. Save them to ini file
        try:
            # Get the content and add to the ini file
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['ip'] = ip
            config['MP2']['tcp_port'] = tcp_port
            config['MP2']['subnet'] = subnet
            config['MP2']['gateway'] = gateway
            config['MP2']['dns1'] = dns1
            config['MP2']['dns2'] = dns2
            config['MP2']['ftp_user'] = ftp_user
            config['MP2']['ftp_password'] = ftp_password
            config['MP2']['ftp_port'] = ftp_port          

            with open(config_path, 'w') as configfile:
                config.write(configfile)
        except Exception as ex:
            return render_template('save_error.html', error="net.html: Error saving info to ini: " + str(ex))
        
        # Everything is hunky dory. Reboot the system
        os.system("nohup sudo -b bash -c 'sleep 2; reboot -f' &>/dev/null;")
        return render_template('submit_ok.html', ip=ip)

    # Else load page
    else:
        ip = '*error*'
        tcp_port = '*error*'
        subnet = '*error*'
        gateway = '*error*'
        dns1 = '*error*'
        dns2 = '*error*'
        ftp_user = '*error*'
        ftp_password = '*error*'
        ftp_port = '*error*'
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            ip = config['MP2']['ip']
            tcp_port = config['MP2']['tcp_port']
            subnet = config['MP2']['subnet']
            gateway = config['MP2']['gateway']
            dns1 = config['MP2']['dns1']
            dns2 = config['MP2']['dns2']
            ftp_user = config['MP2']['ftp_user']
            ftp_password = config['MP2']['ftp_password']
            ftp_port = config['MP2']['ftp_port']
        except Exception as ex:
            print('net.html: Error getting info: ' + str(ex))
        return render_template('net.html', ip=ip, tcp_port=tcp_port, subnet=subnet, gateway=gateway, dns1=dns1, dns2=dns2, ftp_user=ftp_user, \
            ftp_password=ftp_password, ftp_port=ftp_port)

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

            check_input_track(input1_on, input1_on_track, 'Input 1 On')
            check_input_track(input1_off, input1_off_track, 'Input 1 Off')
            check_input_track(input2_on, input2_on_track, 'Input 2 On')
            check_input_track(input2_off, input2_off_track, 'Input 2 Off')

            input1_on_ignore = request.form.get('input1_on_ignore', default='0')
            input1_off_ignore = request.form.get('input1_off_ignore', default='0')
            input2_on_ignore = request.form.get('input2_on_ignore', default='0')
            input2_off_ignore = request.form.get('input2_off_ignore', default='0')

        except Exception as ex:
            print('din.html: Error saving options: ' + str(ex))
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
            print('din.html: Error saving options: ' + str(ex))
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
            # Get the content
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
            print('din.html: Error getting info: ' + str(ex))
        
        return render_template('din.html', input1_on=input1_on, input1_off=input1_off, input2_on=input2_on, input2_off=input2_off, \
            input1_on_track=input1_on_track, input1_off_track=input1_off_track, input2_on_track=input2_on_track, input2_off_track=input2_off_track, \
            input1_on_ignore=input1_on_ignore, input1_off_ignore=input1_off_ignore, input2_on_ignore=input2_on_ignore, input2_off_ignore=input2_off_ignore)

# Digital outputs page
@app.route('/dout.html', methods=['POST', 'GET'])
def dout():
    # If user has pressed "Save"
    if request.method == 'POST':
        try:
            # Get the content and make sure it's kosher
            output1 = request.form['output1']
            output2 = request.form['output2']

            output1_track = request.form['output1_track']
            output2_track = request.form['output2_track']

            check_output_track(output1, output1_track, 'Output 1')
            check_output_track(output2, output2_track, 'Output 2')

        except Exception as ex:
            print('dout.html: Error saving options: ' + str(ex))
            return render_template('save_error.html', error="dout.html: Value error: " + str(ex))

        # Values are okay. Save to ini file
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['output1'] = output1
            config['MP2']['output2'] = output2

            config['MP2']['output1_track'] = output1_track
            config['MP2']['output2_track'] = output2_track

            ip = config['MP2']['ip']

            with open(config_path, 'w') as configfile:
                config.write(configfile)

        except Exception as ex:
            print('dout.html: Error saving options: ' + str(ex))
            return render_template('save_error.html', error="dout.html: Error saving options to ini: " + str(ex))

        return render_template('submit_ok.html', ip=ip)

    # Else load page
    else:
        output1 = ''
        output2 = ''
        output1_track = '0'
        output2_track = '0'

        try:
            # Get the content
            config = configparser.ConfigParser()
            config.read(config_path)
            output1 = config['MP2']['output1']
            output2 = config['MP2']['output2']
            output1_track =  config['MP2']['output1_track']
            output2_track = config['MP2']['output2_track']

        except Exception as ex:
            print('dout.html: Error getting info: ' + str(ex))
        
        return render_template('dout.html', output1=output1, output2=output2, output1_track=output1_track, output2_track=output2_track)

# Others page
@app.route('/oth.html', methods=['POST', 'GET'])
def oth():
    # If user has pressed "Save"
    if request.method == 'POST':
        try:
            # Get the content and make sure it's kosher
            auto_start = request.form.get('auto_start', default='0')
            auto_start_track = request.form['auto_start_track']

            # If user selected auto start, make sure there is a track number
            if (auto_start == '1') and (auto_start_track == ''):
                raise ValueError('Auto start selected, but not track number entered')

        except Exception as ex:
            print('oth.html: Error saving options: ' + str(ex))
            return render_template('save_error.html', error="oth.html: Value error: " + str(ex))

        # Values are okay. Save to ini file
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            config['MP2']['auto_start'] = auto_start
            config['MP2']['auto_start_track'] = auto_start_track

            ip = config['MP2']['ip']

            with open(config_path, 'w') as configfile:
                config.write(configfile)

        except Exception as ex:
            print('oth.html: Error saving options: ' + str(ex))
            return render_template('save_error.html', error="oth.html: Error saving options to ini: " + str(ex))

        return render_template('submit_ok.html', ip=ip)

    # Else load page
    else:
        auto_start = '0'
        auto_start_track = '0'

        try:
            # Get the content
            config = configparser.ConfigParser()
            config.read(config_path)
            auto_start = config['MP2']['auto_start']
            auto_start_track = config['MP2']['auto_start_track']

        except Exception as ex:
            print('oth.html: Error getting info: ' + str(ex))
        
        return render_template('oth.html', auto_start=auto_start, auto_start_track=auto_start_track)


# Network data error
@app.route('/netdata_error.html')
def netdata_error():
    return render_template('netdata_error.html')

# Save error page. Shown when there is an error saving data
@app.route('/save_error.html')
def save_error():
    return render_template('save_error.html')

# Submit successful page. Shown after successful save
@app.route('/submit_ok.html')
def submit_ok():
    return render_template('submit_ok.html')

# General error (currently unused, but we'll keep it)
@app.route('/gen_error.html')
def gen_error():
    return render_template('gen_error.html')

############################################################################
# Helper functions
############################################################################
def is_valid_ipv4(ip):
    """A little regex to check if the ip is valid ipv4"""
    return re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip) 

def check_input_track(action, track_number, io):
    """ Checks track given for I/O input and makes sure its kosher """
    if action == "play" or action == "loop" or action == "random":
        if track_number == '':
            raise ValueError('Action ' + action + ' specified for ' + io + ' but no track number entered')

def check_output_track(action, track_number, io):
    """ Checks track given for I/O output and makes sure its kosher """
    if action == "on_track" or action == "pulse_track":
        if track_number == '':
            raise ValueError('Action ' + action + ' specified for ' + io + ' but no track number entered')

def run_web_server(host):
    """Runs the webserver in a seperate thread"""
    server_thread = threading.Thread(target=app.run, kwargs={'host':host, 'port':8080}, daemon=True)
    server_thread.start()

    
# if __name__ == "__main__":
#     """Runs the webserver"""
#     app.run()
#     app.run(host=host, port=8080)

