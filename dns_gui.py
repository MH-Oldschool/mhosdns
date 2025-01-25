import socket
import threading
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from dns_server import DNSServer


class DNSApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the DNS server
        self.dns_server = DNSServer()

        # Connect the signals from the DNS server to the respective slot functions
        self.dns_server.server_info.connect(self.on_server_info)
        self.dns_server.server_error.connect(self.on_server_error)

        # Get local IP address and store it globally
        self.local_ip = self.get_local_ip()

        # Set up the GUI
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('MHOS DNS Server v0.1')

        # Fixed window size and prevent resizing
        self.setFixedSize(400, 200)

        # Create widgets
        self.label_ip = QLabel(f'Local IP: {self.local_ip}', self)
        self.start_button = QPushButton('Start Server', self)
        self.stop_button = QPushButton('Stop Server', self)
        self.status_label = QLabel('', self)

        # Style for error message (initially empty)
        self.status_label.setStyleSheet('font-weight: bold;')
        self.status_label.setAlignment(Qt.AlignCenter)

        # Center the IP label and reduce margin on top
        self.label_ip.setAlignment(Qt.AlignCenter)

        # Connect buttons to functions
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.label_ip, 0, Qt.AlignCenter)  # Center IP label
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)

        # Set the layout for the main window
        self.setLayout(layout)

    def get_local_ip(self):
        """ Get the local IP address of the machine """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Connecting to a bogon IP address remote address to get local IP
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'  # If anything goes wrong, fall back to localhost
        finally:
            s.close()
        return ip

    def start_server(self):
        """ Start the DNS server """
        # Start the DNS server in a separate thread
        self.dns_server_thread = threading.Thread(target=self.dns_server.start_server, args=(self.local_ip,))
        self.dns_server_thread.daemon = True
        self.dns_server_thread.start()

    def stop_server(self):
        """ Stop the DNS server """
        if self.dns_server.stop_server():
            self.on_server_info('DNS server stopped')
        else:
            self.on_server_info('DNS server is not running')

    def on_server_info(self, message):
        """ Slot to handle when the server starts successfully """
        self.update_status_message(message, color=QColor(0, 0, 255))  # Blue for info

    def on_server_error(self, error_message):
        """ Slot to handle when there is an error starting the server """
        self.update_status_message(error_message, color=QColor(255, 0, 0))  # Red for errors

    def update_status_message(self, message, color):
        """ Update the error label with the appropriate message and color """
        if len(message) > 63:
            message = message[:60] + '...'
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f'color: {color.name()}; font-weight: bold;')

    # override
    def closeEvent(self, event):
        """ Override the closeEvent to ensure the server is stopped when the window is closed """
        if self.dns_server.is_running:
            self.stop_server()  # Stop the server if it's running
        event.accept()  # Close the window
