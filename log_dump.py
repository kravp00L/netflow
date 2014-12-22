'''
################################################################
# 
# Python script to export netflow data to ASCII text
#   
################################################################
'''
import os
import sys
import shutil
import subprocess
import pdb

CONFIG_FILE = 'listener.conf'
BINARY_NAME = 'nfdump'

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
        print ''.join(['Exception in read_config: ', str(err)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in read_config:', str(e)])
    return params

def get_export_filename(filename):
    filename_elements = str(filename).split('.')
    export_filename = ''.join(
                            [
                            str(filename_elements[1]),
                            '_csv_',
                            str(filename_elements[0]),
                            '.log'
                            ]
                        )
    return export_filename

def move_file_to_archive(file, params):
    success = False
    archive_path = params.get('archive_path')
    log_path = params.get('bin_log_path')
    try:
        shutil.move(
            ''.join([log_path,'/',file]),
            ''.join([archive_path,'/',file])
        )
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in move_file_to_archive:', str(e)])
    return success

def export_netflow_data(params):
    archive_path = params.get('archive_path')
    export_path = params.get('ascii_log_path')
    log_path = params.get('bin_log_path')
    bin_path = params.get('nfcapd_path')    
    try:
        files = os.listdir(log_path)
        for f in files:
            if not 'current' in f:
                this_file = ''.join([log_path,'/',f])
                if os.path.isfile(this_file):              
                    export_file = get_export_filename(f)
                    p = subprocess.Popen(
                        [
                        ''.join([bin_path,'/',BINARY_NAME]),
                        '-q',
                        '-r',
                        this_file,
                        '-o',
                        'csv',
                        ], 
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )                                       
                    (std_out, std_err) = p.communicate()                    
                    with open(os.path.join(export_path,export_file),'w') as dump_file:
                        dump_file.write(std_out)
                    move_file_to_archive(f, params)
        success = True
    except OSError as err:
        print ''.join(['Exception in export_netflow_data: ',str(err)])
    except ValueError as ve:
        print ''.join(['Exception in export_netflow_data: ',str(ve)])
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in export_netflow_data:', str(e)])

def main():
    params = read_config()
    export_netflow_data(params)
    
if __name__ == "__main__":
    main()
