import socket
import threading
import dnslib
import configparser
import os
from PyQt5.QtCore import pyqtSignal, QObject


# noinspection PyUnresolvedReferences
class DNSServer(QObject):
    server_info = pyqtSignal(str)  # Signal for server information
    server_error = pyqtSignal(str)  # Signal for errors (e.g., permission issues)

    def __init__(self, config_file='domains.conf'):
        super().__init__()
        self.config_file = config_file
        self.domains = {}
        self.load_config()
        self.server_socket = None
        self.server_thread = None
        self.is_running = False

    def load_config(self):
        """ Load domain to IP mappings from the config file or fallback dictionary """

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)
            for section in config.sections():
                domain = section.strip()
                ip = config.get(section, 'ip').strip()
                self.domains[domain] = ip
        else:
            # Fallback to hardcoded dictionary if config file is not present
            self.domains = {
                '*.dnas.playstation.org': '34.75.107.68',
                '*.kddi-mmbb.jp': '151.80.238.101',
                'corsair.capcom.co.jp': '151.80.238.99',
                'skyhawk.capcom.co.jp': '151.80.238.99',
                'viper.capcom.co.jp': '151.80.238.99',
                'crusader.capcom.co.jp': '151.80.238.99',
                'raptor.capcom.co.jp': '151.80.238.99',
                'strike-raptor.capcom.co.jp': '151.80.238.99',
                'goshawk.capcom.co.jp': '151.80.238.104',
                'spector.capcom.co.jp': '151.80.238.104',
                'meteor.capcom.co.jp': '151.80.238.104',
                'voodoo.capcom.co.jp': '151.80.238.104'
            }
    
    def handle_request(self, data, addr):
        """ Handle incoming DNS requests """
        request = dnslib.DNSRecord.parse(data)
        response = request.reply()

        qname = str(request.q.qname).lower().strip().rstrip('./')
        print(f'Received DNS request for: {qname}')
        
        # Check for exact match first
        ip = self.domains.get(qname)
        
        if not ip:
            # If no exact match, check for wildcard matches
            for domain, dest_ip in self.domains.items():
                if domain.startswith('*.'):
                    if qname.endswith(domain.replace('*.', '')):
                        ip = dest_ip
                        break
                    
        if ip:
            response.add_answer(dnslib.RR(qname, dnslib.QTYPE.A, rdata=dnslib.A(ip), ttl=60))
        else:
             # Forward request to local DNS server if no match found
            try:
                print('Domain not found, fallback to local DNS resolver')
                # Use the system's default DNS resolver
                resolver = socket.gethostbyname_ex
                try:
                    _, _, ip_list = resolver(qname)
                    ip = ip_list[0]  # Use the first IP from the list
                    response.add_answer(dnslib.RR(qname, dnslib.QTYPE.A, rdata=dnslib.A(ip), ttl=60))
                except socket.gaierror:
                    # If name resolution fails, use NXDOMAIN
                    response.header.rcode = dnslib.RCODE.NXDOMAIN
            except Exception as e:
                print(f'Error resolving DNS: {e}')
                response.header.rcode = dnslib.RCODE.NXDOMAIN
        
        if response.header.rcode == dnslib.RCODE.NXDOMAIN:
            self.server_error.emit(f'[{qname}] not found')
        else:
            self.server_info.emit(f'[{qname}] resolved')

        self.server_socket.sendto(response.pack(), addr)

    def start_server(self, local_ip):
        """ Start the DNS server to listen on the provided IP address and port 53 """
        if self.is_running:
            print('Server is already running')
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Use SO_REUSEADDR if SO_REUSEPORT doesn't exist
        except AttributeError:
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Try binding to the provided local IP address
            self.server_socket.bind((local_ip, 53))
            self.is_running = True
            self.server_info.emit(f'DNS server started on {local_ip}')
        except PermissionError:
            self.server_error.emit('Error: You need admin privileges to run on port 53.')
            return
        except Exception as e:
            self.server_error.emit(f'Error: {str(e)}')
            return

        while self.is_running:
            data, addr = self.server_socket.recvfrom(512)
            #threading.Thread(target=self.handle_request, args=(data, addr)).start()
            self.handle_request(data, addr)

    def stop_server(self):
        """ Stop the DNS server """
        if not self.is_running:
            print('Server is not running')
            return False

        self.is_running = False
        self.server_socket.close()
        print('DNS server stopped')
        return True
