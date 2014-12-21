'''
#####################################################################
#
# Script to read parameter files for Netflow collection
#
##################################################################### 
'''
import datetime
import os
import sys

CONFIG_FILE = 'listener.conf'

def get_config_file():
    apps_base_dir = os.path.join(os.environ["NETFLOW_HOME"], 'conf')
    default_file = os.path.join(app_path, 'default', CONFIG_FILE)
    local_file = os.path.join(app_path, 'local', CONFIG_FILE)    
    if os.path.exists(local_file) and os.path.isfile(local_file):
        return local_file
    else:
        return default_file

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
                        print ''.join(['DEBUG: ',str(c_param[0].strip()),' : ',str(c_param[1].strip())])
                        params[c_param[0].strip()] = c_param[1].strip()
                        line = f.next()
                elif '[listener]' in line.strip():
                    this_listener = dict()
                    line = f.next()
                    while len(line.strip()) > 0:
                        c_param = (line.strip()).split('=')
                        print ''.join(['DEBUG: ',str(c_param[0].strip()),' : ',str(c_param[1].strip())])
                        this_listener[c_param[0].strip()] = c_param[1].strip()
                        line = f.next()
                    listeners.append(this_listener)
    except IOError as err:
        print ''.join(['Exception: ', str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in read_config:', str(e)])
    return params, listeners

def main():
    params, listeners = read_config()
        
if __name__ == "__main__":
    main()
