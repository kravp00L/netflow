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

def check_uid():
    try:
        privs = False
        p = subprocess.Popen(['id'],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (out, err) = p.communicate()
        if out.find('uid=0') >= 0:
            privs = True
        return privs
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in checking permissions for user context:', str(e)])
    
def show_intro():
    print ''.join(['NetFlow collector v',VERSION,'\n'])
    print 'This script will configure NetFlow collection on this system '
    print 'using nfcapd.  The nfdump tools should be installed on the system '
    print 'prior to executing this script.  The nfdump tools can be found at '
    print 'http://nfdump.sourceforge.net/ and should be compiled locally.'
    print '\n'
    print 'The script will also create the configuration stanzas for sending '
    print 'the data to a Splunk instance. If your target output system is '
    print 'something different, you should modify the script prior to execution '
    print 'to meet the specific needs of your target. '
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
            sys.exit(0)
        except:    
            print 'Error processing your selection'      
    return listener_count

def get_retention_interval():
    retention_interval = DEFAULT_LOG_SAVE_DAYS
    message = ''.join(
        [
        'Number of days to keep exported ASCII flow logs [Default: ',
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
                                   ' days to retain exported ASCII flow logs.'])
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
            sys.exit(0)
        except:    
            print 'Error processing your selection'      
    return retention_interval

def get_rollover_interval():
    rollover_cycle = DEFAULT_LOG_ROLLOVER
    message = ''.join(
        [
        'Number of seconds between rollover of flow capture ',
        'files [Default: ', 
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
            sys.exit(0)
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
#        else:
#            print ''.join(['Using default index ',index_name])
    except KeyboardInterrupt:
            sys.exit(0)
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
            sys.exit(0)
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
#                print ''.join(['Using default of UDP port ',str(bind_port)])
                break
        except KeyboardInterrupt:
            sys.exit(0)
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
            sys.exit(0)
        except:
            print 'Error encountered validating path. Using current directory.'
    return installPath
        
def get_nfcapd_path():
    nfcapd_binary = '/usr/local/bin/nfcapd'
    if not (os.path.exists(nfcapd_binary) and os.path.isfile(nfcapd_binary)):
        p = subprocess.Popen(
            [
            'find',
            '/',
            '-name',
            'nfcapd',
            '-print'
            ],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (out, err) = p.communicate()
        for result in out:
            if result.find('home') == -1:
                nfcapd_binary = result
                break
    return nfcapd_binary

def get_nfdump_path():
    nfdump_binary = '/usr/local/bin/nfdump'
    if not (os.path.exists(nfdump_binary) and os.path.isfile(nfdump_binary)):
        p = subprocess.Popen(
            [
            'find',
            '/',
            '-name',
            'nfdump',
            '-print'
            ],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (out, err) = p.communicate()
        for result in out:
            if result.find('home') == -1:
                nfdump_binary = result
                break
    return nfdump_binary    

def create_output_directories(install_path):
    try:
        for f in [BINARY_LOG_DIR, ASCII_LOG_DIR, ARCHIVE_LOG_DIR]:
            current_dir = os.path.join(install_path, 'data', f)
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)        
    except:
        if not os.path.isdir(current_dir):
            print 'Error creating output directory. File with same name exists.'
            raise

def create_config_directory(install_path):
    try:
        local_dir = os.path.join(install_path, 'conf')
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)        
    except:
        if not os.path.isdir(local_dir):
            print 'Error creating output directory. File with same name exists.'
            raise
            
def write_inputs_file(install_path, index_name):
    success = False
    file_name = os.path.join(install_path, 'conf','inputs.conf')
    try:
        with open(file_name,'w') as f:
            f.write(''.join(['[monitor://',install_path,'/',ASCII_LOG_DIR,']']))
            f.write('\n')
            f.write(''.join(['index = ',index_name]))        
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
    file_name = os.path.join(install_path, 'conf','indexes.conf')
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

def write_props_file(install_path):
    success = False
    file_name = os.path.join(install_path, 'conf','props.conf')
    try:
        with open(file_name,'w') as f:
            f.write('[netflow]')
            f.write('\n')
            f.write('CHECK_FOR_HEADER = false')
            f.write('\n')
            f.write('SHOULD_LINEMERGE = false')
            f.write('\n')
            f.write('REPORT-netflow_field_extract = netflow_csv')
            f.write('\n')
            f.write('FIELDALIAS-src = src_ip AS src')
            f.write('\n')
            f.write('FIELDALIAS-dst = dst_ip AS dst')
            f.write('\n')
            f.write('FIELDALIAS-input_bytes = input_bytes AS bytes')
            f.write('\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in write_props_file:', str(e)])
        print ''.join(['Error while writing out file ', file_name])
    return success

def write_transforms_file(install_path):
    success = False
    file_name = os.path.join(install_path, 'conf','transforms.conf')
    try:
        with open(file_name,'w') as f:
            f.write('[netflow_csv]')
            f.write('\n')
            f.write('DELIMS = ","')
            f.write('\n')
            f.write('FIELDS = "flow_start_time", "flow_end_time", "flow_duration", "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "tcp_flag", "fwd_status", "src_tos", "input_pkts", "input_bytes", "output_pkts", "output_bytes", "in_if", "out_if", "src_bgp_as", "dst_bgp_as", "src_mask", "dst_mask", "dst_tos", "flow_dir", "next_hop_rtr", "bgp_next_hop_rtr", "src_vlan", "dest_vlan", "in_src_mac", "out_dst_mac", "in_dst_mac", "out_src_mac", "mpls1", "mpls2", "mpls3", "mpls4", "mpls5", "mpls6", "mpls7", "mpls8", "mpls9", "mpls10", "client_latency", "server_latency", "app_latency", "rtr_ip", "engine", "exp_sys_id", "flow_received"')
            f.write('\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in write_transforms_file:', str(e)])
        print ''.join(['Error while writing out file ', file_name])
    return success

def write_listener_config_file(install_path, log_timespan,
                                log_lifetime, listeners):
    success = False
    file_name = os.path.join(install_path, 'conf','listener.conf')
    try:
        with open(file_name,'w') as f:
            f.write('[global]')
            f.write('\n')
            f.write(''.join(['archive_path = ',install_path,'/data/',ARCHIVE_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['ascii_log_path = ',install_path,'/data/',ASCII_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['bin_log_path = ',install_path,'/data/',BINARY_LOG_DIR]))
            f.write('\n')
            f.write(''.join(['nfcapd_path = ',get_nfcapd_path()]))
            f.write('\n')
            f.write(''.join(['nfdump_path = ',get_nfdump_path()]))
            f.write('\n')
            f.write(''.join(['rollover_secs = ',str(log_timespan)]))
            f.write('\n')
            f.write(''.join(['retention_days = ',str(log_lifetime)]))
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

def create_schedule(install_path):
    # TODO: Directly write to crontab?
    # (crontab -u userhere -l; echo "$line" ) | crontab -u userhere -
    success = False
    listener_sched = '0/5 * * * * '
    dump_sched = '0/1 * * * * '
    cleanup_sched = '30 22 * * * '
    file_name = os.path.join(install_path, 'conf','cron.entries')
    try:
        with open(file_name,'w') as f:
            f.write('# Add the entries below to crontab for root')
            f.write('\n')
            f.write(''.join([listener_sched,'python ',install_path,'/',DAEMON_SCRIPT]))
            f.write('\n')
            f.write(''.join([dump_sched,'python ',install_path,'/',DUMP_SCRIPT]))
            f.write('\n')
            f.write(''.join([cleanup_sched,'python ',install_path,'/',CLEANUP_SCRIPT]))
            f.write('\n')
        success = True
    except:
        e = sys.exc_info()[0]
        print ''.join(['Exception in create_schedule:', str(e)])
        print ''.join(['Error while writing out file ', file_name])
    return success
   
# program execution 
def main():
    success = False
    is_root = check_uid()
    if not (is_root):
        print 'Script must be run as root. Exiting.'
        sys.exit(1)
    show_intro()
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
        pidfile = ''.join(['nfcapd',str(counter),'_',
                            ip,'_',str(port),'.pid'])
        this_listener = [counter,ip,port,pidfile]
        listeners.append(this_listener)
        counter += 1
    create_config_directory(path)
    create_output_directories(path)
    create_schedule(path)
    index = get_index_name()
    index_success = write_index_file(path,index) 
    input_success = write_inputs_file(path,index)
    props_success = write_props_file(path)
    transforms_success = write_transforms_file(path)
    listener_success = write_listener_config_file(path,rollover,logdays,listeners)
    success = index_success and input_success and listener_success and props_success and transforms_success
    if (success):
        print 'Configuration complete.'
        sys.exit(0)
    else:
        print 'Error during configuration. Please re-run configuration script.'
        sys.exit(1)
        
if __name__ == "__main__":
    main()
