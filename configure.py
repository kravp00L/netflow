'''
#####################################################################
# 
# Python script to configure netflow collection
#
#####################################################################
'''
import os
import sys
import subprocess
import socket
import pdb

# custom exceptions
class OperatingSystemException( Exception ): pass
class PriviligedPortException( Exception ): pass

# constants and default values
VERSION = '1.0.0'
DAEMON_SCRIPT = 'netflow.py'
DUMP_SCRIPT = 'log_dump.py'
CLEANUP_SCRIPT = 'log_cleanup.py'
BINARY_LOG_DIR = 'nfdump-binary'
ASCII_LOG_DIR = 'nfdump-ascii'
ARCHIVE_LOG_DIR = 'nfdump-archive'
MIN_LISTENERS = 1
MAX_LISTENERS = 5
DEFAULT_INDEX = 'netflow'
DEFAULT_LISTENER_COUNT = 1
DEFAULT_LOG_ROLLOVER = 120
DEFAULT_LOG_SAVE_DAYS = 3
MIN_LOG_SAVE_DAYS = 1
MAX_LOG_SAVE_DAYS = 180
DEFAULT_BIND_IP = '0.0.0.0'
DEFAULT_BIND_PORT = 9995
MIN_BIND_PORT = 1024
MAX_BIND_PORT = 65536

def show_intro():
    print ''.join(['NetFlow collector v',VERSION,'\n'])
    print 'This script will configure NetFlow collection on this system '
    print 'using nfcapd.  The nfdump tools should be installed on the system '
    print 'prior to executing this script.  The nfdump tools can be found at '
    print 'http://nfdump.sourceforge.net/ and should be compiled locally.'
    print '\n'
    print 'The script will also create configuration files for sending the data '
    print 'to a Splunk instance.  The script expects Splunk Enterprise or a Splunk '
    print 'forwarder to be installed on the system.   If your target output system is '
    print 'something different, you should modify the script prior to execution to meet '
    print 'the specific needs of your target. '
    print '\n'

def get_listener_count():
    listener_count = DEFAULT_LISTENER_COUNT
    message = ''.join(
        [
        'How many listeners would you like to configure? [Default: ',
        str(DEFAULT_LISTENER_COUNT) ,']: '
        ]
    )
    while True:
        response = raw_input(message)
        try:
            if len(response) > 0:
                listener_count = int(response.strip())
                if not MIN_LISTENERS <= listener_count <= MAX_LISTENERS:
                    print ''.join(
                        [
                        'You selected ', str(listener_count),
                                ' listeners for this system.'
                        ]
                    )
                    print 'This selection is not permitted.'
                    print ''.join(
                        [
                        'Please select between ',
                        str(MIN_LISTENERS),' and ',str(MAX_LISTENERS),
                        ' listeners.'
                        ]
                    )
                else:
                    break
            else:
                listener_count = DEFAULT_LISTENER_COUNT
                break
        except KeyboardInterrupt:
            sys.exit()
        except:    
            print 'Error processing your selection'      
    return listener_count

def get_retention_interval():
    retention_interval = DEFAULT_LOG_SAVE_DAYS
    message = ''.join(
        [
        'Number of days to keep binary flow logs [Default: ',
        str(DEFAULT_LOG_SAVE_DAYS),']: '
        ]
    )
    while True:    
        response = raw_input(message)
        try:
            if len(response) > 0:
                retention_interval = int(response.strip())
                if not MIN_LOG_SAVE_DAYS <= retention_interval <= MAX_LOG_SAVE_DAYS:
                    print ''.join(['You selected ', str(retention_interval),
                                   ' days to retain binary flow logs.'])
                    print 'This selection is not permitted.'
                    print ''.join(['Please select between ',
                        str(MIN_LOG_SAVE_DAYS),' and ',
                        str(MAX_LOG_SAVE_DAYS),' days.'])
                else:
                    break
            else:
                retention_interval = DEFAULT_LOG_SAVE_DAYS
                break
        except KeyboardInterrupt:
            sys.exit()
        except:    
            print 'Error processing your selection'      
    return retention_interval

def get_rollover_interval():
    rollover_cycle = DEFAULT_LOG_ROLLOVER
    message = ''.join(
        [
        'Number of seconds between rollover of flow capture ',
        'files for indexing [Default: ', 
        str(DEFAULT_LOG_ROLLOVER),']: '
        ]
    )
    while True:    
        response = raw_input(message)
        try:
            if len(response) > 0:
                rollover_cycle = int(response.strip())
                print ''.join(['You selected ', str(rollover_cycle),
                                   ' seconds to rollover flow capture files.'])
                break
            else:
                rollover_cycle = DEFAULT_LOG_ROLLOVER
                break
        except KeyboardInterrupt:
            sys.exit()
        except:    
            print 'Error processing your selection'      
    return rollover_cycle

def get_index_name():
    index_name = DEFAULT_INDEX
    message = ''.join(
        [
        'Name of Splunk index to use [Default: ',
        DEFAULT_INDEX,
        ']: '
        ]
    )
    try:
        response = str(raw_input(message)).strip()
        if len(response) > 0:
            index_name = response
        else:
            print ''.join(['Using default index ',index_name])
    except KeyboardInterrupt:
            sys.exit()
    except:
        print 'Error processing your Index selection.'
        sys.exit(1) 
    return index_name

def validate_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False
    return True
    
def validate_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True
    
def check_bind_port(address,port):
    isvalid = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((address, port))
        s.close()
        isvalid = True
    except socket.error:
        print 'Unable to bind socket to port.  In use?'
    except:
        print 'Exception in check_bind_port function.'
    return isvalid

def get_bind_address():
    bind_ip = DEFAULT_BIND_IP
    message = ''.join(
        [
        'Specify IPv4 or IPv6 address to bind to listener ',
        '[Default: ',DEFAULT_BIND_IP,']: '
        ]
    )
    while True:
        try:
            response = str(raw_input(message)).strip()
            if len(response) > 0:
                if validate_ipv4_address(response):
                    bind_ip = response
                    break
                elif validate_ipv6_address(response):
                    bind_ip = response
                    break
                else:
                    print 'Invalid entry for IPv4 or IPv6 address.'
            else:
                bind_ip = DEFAULT_BIND_IP    
                break
        except KeyboardInterrupt:
            sys.exit()
        except:
            print 'Error processing your address selection.'
    return bind_ip
    
def get_bind_port():
    bind_port = DEFAULT_BIND_PORT
    message = ''.join(
        [
        'Specify UDP port to listen on [Default: ',
        str(DEFAULT_BIND_PORT),']: '
        ]
    )
    while True:
        try:
            response = raw_input(message)
            if len(response) > 0:
                bind_port = int(response.strip())
                if 0 < bind_port < MIN_BIND_PORT:
                    print ''.join(['UDP port ', str(bind_port), 
                                    ' is in the privileged port range.'])
                    confirm = str(raw_input('Are you sure [Y/N]? ')).strip()
                    if not confirm.lower() in ['y','yes']:
                        raise PriviligedPortException
                    else:
                        break
                elif (MIN_BIND_PORT < bind_port < MAX_BIND_PORT):
                    break
                else:
                    print 'Invalid port selection.'
            else:                
                bind_port = DEFAULT_BIND_PORT
                print ''.join(['Using default of UDP port ',str(bind_port)])
                break
        except KeyboardInterrupt:
            sys.exit()
        except PriviligedPortException:
            print ''.join(['Please select a port above ',str(MIN_BIND_PORT)])
        except:
            print 'Error processing your port selection.'            
    return bind_port

def get_install_path():
    installPath = os.getcwd()
    displaytext = ''.join(
        [
        'Path for NetFlow scripts ',
        '[', installPath, ']: '
        ]
    )
    while True:
        try:
            response = str(raw_input(displaytext)).strip()
            if len(response) > 0:
                if (os.path.exists(response)):
                    installPath = response
                else:
                    print 'Unable to validate selected path. Please re-enter.'
            else:
                break
        except KeyboardInterrupt:
            sys.exit()
        except:
            print 'Error encountered validating path. Using current directory.'
    return installPath
        
def create_output_directories(install_path):
    try:
        for f in [BINARY_LOG_DIR, ASCII_LOG_DIR, ARCHIVE_LOG_DIR]:
            current_dir = os.path.join(install_path, f)
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)        
    except:
        if not os.path.isdir(current_dir):
            print 'Error creating output directory. File with same name exists.'
            raise

def create_local_config_directory(install_path):
    try:
        local_dir = os.path.join(install_path, 'local')
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)        
    except:
        if not os.path.isdir(local_dir):
            print 'Error creating output directory. File with same name exists.'
            raise
            
def set_path_owner(install_path):
    try:
        p = subprocess.Popen(
            [
            'chown',
            '-R',
            'splunk:splunk',
            install_path
            ],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (out, err) = p.communicate()                            
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in set_path_owner:', str(e)])
        print ''.join(['Error setting owner for ', install_path])
    
def set_path_permissions(install_path):
    try:
        p = subprocess.Popen(
            [
            'chmod',
            '-R',
            '755',
            install_path
            ],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (out, err) = p.communicate()                                                        
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in set_path_permissions:', str(e)])
        print ''.join(['Error setting permissions on ', install_path])
        
def write_inputs_file(install_path, index_name):
    success = False
    file_name = os.path.join(install_path, 'local','inputs.conf')
    try:
        with open(file_name,'w') as f:
            f.write(''.join(['[monitor://',install_path,'/',ASCII_LOG_DIR,']']))
            f.write('\n')
            f.write(''.join(['index = ',index_name]))        
            f.write('\n')
            f.write('sourcetype = netflow')
            f.write('\n')
            f.write('disabled = false')
            f.write('\n\n')
            f.write(''.join(['[script://',install_path,'/bin/',DAEMON_SCRIPT,']']))
            f.write('\n')
            f.write(''.join(['index = ',index_name]))        
            f.write('\n')
            f.write('interval = 300')
            f.write('\n')
            f.write('sourcetype = netflow')
            f.write('\n')
            f.write('disabled = false')
            f.write('\n\n')
            f.write(''.join(['[script://',install_path,'/bin/',DUMP_SCRIPT,']']))
            f.write('\n')
            f.write(''.join(['index = ',index_name]))        
            f.write('\n')
            f.write('interval = 600')
            f.write('\n')
            f.write('sourcetype = netflow')
            f.write('\n')
            f.write('disabled = false')
            f.write('\n\n')
            f.write(''.join(['[script://',install_path,'/bin/',CLEANUP_SCRIPT,']']))
            f.write('\n')
            f.write(''.join(['index = ',index_name]))        
            f.write('\n')
            f.write('interval = 86400')
            f.write('\n')
            f.write('sourcetype = netflow')
            f.write('\n')
            f.write('disabled = false')
            f.write('\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in write_inputs_file:', str(e)])
        print ''.join(['Error while writing out file ', file_name])
    return success

def write_index_file(install_path, index_name):
    success = False
    file_name = os.path.join(install_path, 'local','indexes.conf')
    try:
        with open(file_name,'w') as f:
            f.write(''.join(['[',index_name,']']))
            f.write('\n')
            f.write(''.join(['homePath  ',' = $SPLUNK_DB/',index_name,'/db']))
            f.write('\n')
            f.write(''.join(['coldPath  ',' = $SPLUNK_DB/',index_name,'/colddb']))
            f.write('\n')
            f.write(''.join(['thawedPath',' = $SPLUNK_DB/',index_name,'/thaweddb']))
            f.write('\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in write_index_file:', str(e)])
        print ''.join(['Error while writing out file ', file_name])    
    return success

def write_listener_config_file(install_path, sysinfo, log_timespan,
                                log_lifetime, listeners):
    success = False
    file_name = os.path.join(install_path, 'local','listener.conf')
    try:
        with open(file_name,'w') as f:
            f.write('[global]')
            f.write('\n')
            f.write(''.join(['binLogPath  = ',install_path,'/',BINARY_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['asciiLogPath = ',install_path,'/',ASCII_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['archivePath = ',install_path,'/',ARCHIVE_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['nfcapdPath = ',install_path,'/bin/',sysinfo[3]]))
            f.write('\n')
            f.write(''.join(['rolloverInterval = ',str(log_timespan)]))
            f.write('\n')
            f.write(''.join(['retentionInterval = ',str(log_lifetime)]))
            f.write('\n\n')
            for listener in listeners:
                f.write('[listener]')
                f.write('\n')
                f.write(''.join(['listener_id = ',str(listener[0])]))
                f.write('\n')
                f.write(''.join(['listener_bind_ip = ',str(listener[1])]))
                f.write('\n')
                f.write(''.join(['listener_bind_port = ',str(listener[2])]))
                f.write('\n')
                f.write(''.join(['listener_pid_file = ',str(listener[3])]))
                f.write('\n\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in write_listener_config_file:', str(e)])
        print ''.join(['Error while writing out file ', file_name])    
    return success

# program execution 
def main():
    try:
        success = False
        show_intro()
        print 'This process will overwrite indexes.conf, inputs.conf, and listener.conf'
        path = get_install_path()
        rollover = get_rollover_interval();
        logdays = get_retention_interval();
        listener_count = get_listener_count();
        counter = 0
        listeners = []
        while counter < listener_count:
            ip = get_bind_address();
            port = get_bind_port();
            check_bind_port(ip,port)
            pidfile = ''.join(['nfcapd_listener',str(counter),'_',
                                ip,'_',str(port),'.pid'])
            this_listener = [counter,ip,port,pidfile]
            listeners.append(this_listener)
            counter += 1
        create_local_config_directory(path)
        create_output_directories(path)
        index = get_index_name()
        index_success = write_index_file(path,index) 
        input_success = write_inputs_file(path,index)
        listener_success = write_listener_config_file(path,sysinfo,rollover,logdays,listeners)
        set_path_owner(path)
        set_path_permissions(path)
        success = index_success and input_success and listener_success
    except OperatingSystemException:
        print 'Exiting configuration script.'
    except:
        print 'Exception in program execution.'
    if (success):
        print 'Configuration complete.'
        sys.exit(0)
    else:
        print 'Error during configuration. Please re-run configuration script.'
        sys.exit(1)
        
if __name__ == "__main__":
    main()
