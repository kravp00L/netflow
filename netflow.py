'''
################################################################
# 
# Python script to start and monitor nfcapd listeners
#
################################################################
'''
import os
import sys
import subprocess
import socket
import pdb

CONFIG_FILE = 'listener.conf'
BINARY_NAME = 'nfcapd'

def get_config_file():
    app_path = os.path.join('opt', 'netflow', 'conf')
    local_file = os.path.join(app_path, CONFIG_FILE)    
    if os.path.exists(local_file) and os.path.isfile(local_file):
        return local_file
    else:
        sys.exit(1)
    
def read_config():
    params = dict()
    listeners = []
    try:
        with open(get_config_file(),'r') as f:
            for line in f:
                if '[global]' in line.strip():
                    # extracting global parameters
                    line = f.next()
                    while len(line.strip()) > 0:
                        c_param = (line.strip()).split('=')
                        params[c_param[0].strip()] = c_param[1].strip()
                        line = f.next()
                elif '[listener]' in line.strip():
                    this_listener = dict()
                    line = f.next()
                    while len(line.strip()) > 0:
                        c_param = (line.strip()).split('=')
                        this_listener[c_param[0].strip()] = c_param[1].strip()
                        line = f.next()
                    listeners.append(this_listener)
    except IOError as err:
        print ''.join(['Exception: ', str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in read_config:', str(e)])
    return params, listeners

def start_listener(listener, params):
    success = False
    log_path = params.get('bin_log_path')
    bin_path = params.get('nfcapd_path')
    rollover = params.get('rollover_secs')
    bind_ip = listener.get('listener_bind_ip')
    bind_port = listener.get('listener_bind_port')
    pid_file = listener.get('listener_pid_file')
    try:
        p = subprocess.Popen(
            [
            ''.join([bin_path,'/',BINARY_NAME]),
            '-p',
            str(bind_port),
            '-b',
            bind_ip,
            '-T',
            'all',
            '-t',
            str(rollover),
            '-l',
            log_path,
            '-P',
            ''.join([bin_path,'/',pid_file]),
            '-D'
            ], 
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (std_out, std_err) = p.communicate()
        success = True
    except OSError as err:
        print ''.join(['Exception: ',str(err)])
    except ValueError as ve:
        print ''.join(['Exception: ',str(ve)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in start_listener:', str(e)])
    return success    
 
def check_listener_status(listener, params):
    active = False
    bin_path = params.get('nfcapd_path')
    pid_file = listener.get('listener_pid_file')
    file_name = ''.join([bin_path,'/',pid_file])
    try:
        if os.path.isfile(file_name) and os.path.exists(file_name):
            # read file and check status of pid
            with open(file_name) as f:
                line = f.readline()
            pid = int(line.strip())
            p = subprocess.Popen(
                [
                'ps',
                '-p',
                str(pid),
                '-o',
                's='
                ], 
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            (std_out, std_err) = p.communicate()
            if 'S' in std_out.strip():
                active = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in check_listener_status:', str(e)])
    return active

# program execution 
def main():
    params, listeners = read_config()
    for listener in listeners:
        active = check_listener_status(listener, params)
        if not active:
            start_listener(listener, params)
        
if __name__ == "__main__":
    main()
