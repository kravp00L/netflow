'''
################################################################
# 
# Python script to manage netflow log and export files
#   
################################################################
'''
import datetime
import os
import sys

CONFIG_FILE = 'listener.conf'

def get_config_file():
    app_path = os.path.join('opt', 'netflow', 'conf')
    local_file = os.path.join(app_path, CONFIG_FILE)
    if os.path.exists(local_file) and os.path.isfile(local_file):
        return local_file
    else:
        sys.exit(1)

def read_config():
    params = dict()
    try:
        with open(get_config_file(),'r') as f:
            for line in f:
                if '[global]' in line.strip():
                    line = f.next()
                    while len(line.strip()) > 0 and not 'listener' in line.strip():
                        c_param = (line.strip()).split('=')
                        params[c_param[0].strip()] = c_param[1].strip()
                        line = f.next()
    except IOError as err:
        print ''.join(['Exception: ', str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in read_config:', str(e)])
    return params

def cleanup_export_files(params):
    success = False
    export_path = params.get('ascii_log_path')
    retention_interval = params.get('retention_days')
    try:
        files = os.listdir(export_path)
        for f in files:
            if os.path.isfile(''.join([export_path,'/',f])):
                file_mod_ts =  os.path.getmtime(''.join([export_path,'/',f]))
                file_dt = datetime.date.fromtimestamp(file_mod_ts)
                diff = datetime.date.today() - file_dt                
                if diff.days > int(retention_interval):                
                    os.remove(''.join([export_path,'/',f]))
    except OSError as err:
        print ''.join(['Exception: ',str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in cleanup_files:', str(e)])
    return success
    
def cleanup_archived_files(params):
    success = False
    archive_path = params.get('archive_path')
    retention_interval = params.get('retention_days')
    try:
        files = os.listdir(archive_path)
        for f in files:
            if os.path.isfile(''.join([archive_path,'/',f])):
                file_mod_ts =  os.path.getmtime(''.join([archive_path,'/',f]))
                file_dt = datetime.date.fromtimestamp(file_mod_ts)
                diff = datetime.date.today() - file_dt                
                if diff.days > int(retention_interval):                
                    os.remove(''.join([archive_path,'/',f]))
    except OSError as err:
        print ''.join(['Exception: ',str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in cleanup_files:', str(e)])
    return success

def main():
    params = read_config()
    cleanup_archived_files(params)
    cleanup_export_files(params)
        
if __name__ == "__main__":
    main()
