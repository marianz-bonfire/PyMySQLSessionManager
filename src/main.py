import sys
from ui.sessionmanager import SessionManager
from PyQt5.QtWidgets import *

if __name__ == '__main__':
	app = QApplication(sys.argv)
	sessionManager = SessionManager()
	sessionManager.show()
	app.exec_()