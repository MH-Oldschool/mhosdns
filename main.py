import sys
from dns_gui import DNSApp
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon('icon.ico'))
    
    ex = DNSApp()
    ex.show()
    sys.exit(app.exec_())
