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
    apps_base_dir = os.path.join(os.environ["NETFLOW_HOME"], 'conf')
    default_file = os.path.join(app_path, 'default', CONFIG_FILE)
    local_file = os.path.join(app_path, 'local', CONFIG_FILE)    
    if os.path.exists(local_file) and os.path.isfile(local_file):
        return local_file
    else:
        return default_file

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
    export_path = params.get('asciiLogPath')
    retention_interval = params.get('retentionInterval')
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
    archive_path = params.get('archivePath')
    retention_interval = params.get('retentionInterval')
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
