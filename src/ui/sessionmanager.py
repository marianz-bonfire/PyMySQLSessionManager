import atexit
import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from sqlite3 import *


class SessionManager(QDialog):
    def __init__(self):
        atexit.register(self.shutdownEvent)

        currentDir = os.path.dirname(os.path.abspath(__file__))
        dbPath = os.path.join(currentDir, '..', 'db', 'sessions.db')

        self.conn = connect(dbPath)
        self.conn.row_factory = Row
        self.curs = self.conn.cursor()

        self.currentSessionData = {}
        self.sessionIds = []

        self.currentSessionData['hostname'] =''
        self.currentSessionData['database'] = ''
        self.currentSessionData['username'] = ''
        self.currentSessionData['passord'] = ''
        self.currentSessionData['port'] = 3306

        super(SessionManager, self).__init__()
        self.initUI()
        self.loadSessionManager()
        # self.loadSettings()
        self.treeServerManager.setCurrentItem(self.treeServerManager.topLevelItem(0))

    def initUI(self):
        # No session label... TODO: should really move this text to resource file
        self.labelNoSession = QLabel(
            'New here? In order to connect to a MySQL server, you have to create a so called "session" at first. Just click the "New" button on the bottom left to create your first session.\n\nGive it a friendly name (e.g. "Local DB Server") so you\'ll recall it the next time you start HeidiSQL.'
        )
        self.labelNoSession.setWordWrap(True)

        # Setup input fields for settings tab
        checkCompressProtocol = QCheckBox("Compressed client/server protocol")
        checkCompressProtocol.setEnabled(False)
        checkPasswordPrompt = QCheckBox("Prompt")
        checkPasswordPrompt.setEnabled(False)
        comboDatabases = QComboBox()
        comboDatabases.setEditable(True)
        comboDatabases.setEditText("Separated by semicolon")
        comboDatabases.setDisabled(True)
        self.comboNetworkType = QComboBox(self)
        self.comboNetworkType.addItem("TCP/IP")
        self.spinPort = QSpinBox()
        self.spinPort.setRange(0, 65535)
        self.spinPort.setMinimumWidth(65)
        self.textHostname = QLineEdit()
        self.textPassword = QLineEdit()
        self.textPassword.setEchoMode(QLineEdit.Password)
        textStartupScript = QLineEdit()
        textStartupScript.setDisabled(True)
        self.textUser = QLineEdit()

        # Create the Server Manager tree
        self.treeServerManager = QTreeWidget(self)
        self.treeServerManager.header().close()
        self.treeServerManager.setRootIsDecorated(False)
        self.treeServerManager.itemSelectionChanged.connect(
            self.slotServerSelectionChanged
        )

        # Layout for password text field and password check box
        layoutH6 = QHBoxLayout()
        layoutH6.addWidget(self.textPassword)
        layoutH6.addWidget(checkPasswordPrompt)

        # Layout to smallimize the port input field
        layoutH7 = QHBoxLayout()
        layoutH7.addWidget(self.spinPort)
        layoutH7.addStretch(1)

        # Setup the tab widget
        self.tabWidget = QTabWidget(self)
        tabSettings = QWidget()
        tabSettings.tabSettingsLayout = QFormLayout(tabSettings)
        tabSettings.tabSettingsLayout.addRow("Network type:", self.comboNetworkType)
        tabSettings.tabSettingsLayout.addRow("Hostname / IP:", self.textHostname)
        tabSettings.tabSettingsLayout.addRow("User:", self.textUser)
        tabSettings.tabSettingsLayout.addRow("Password:", layoutH6)
        tabSettings.tabSettingsLayout.addRow("Port:", layoutH7)
        tabSettings.tabSettingsLayout.addRow("", checkCompressProtocol)
        tabSettings.tabSettingsLayout.addRow("Databases:", comboDatabases)
        tabSettings.tabSettingsLayout.addRow("Startup script:", textStartupScript)

        self.tabWidget.addTab(
            tabSettings, QIcon("../resources/icons/wrench.png"), "Settings"
        )
        self.tabWidget.setVisible(False)

        # Create the buttons
        buttonNew = QPushButton("New")
        self.buttonSave = QPushButton("Save")
        self.buttonSave.setDisabled(True)
        self.buttonDelete = QPushButton("Delete")
        self.buttonDelete.setDisabled(True)
        self.buttonOpen = QPushButton("Open")
        self.buttonOpen.setDisabled(True)
        buttonCancel = QPushButton("Cancel")

        # Layout for buttons at bottom of session manager
        layoutH4 = QHBoxLayout()
        layoutH4.addWidget(buttonNew)
        layoutH4.addWidget(self.buttonSave)
        layoutH4.addWidget(self.buttonDelete)

        # Layout for session manager pane
        layoutV1 = QVBoxLayout()
        layoutV1.addWidget(QLabel("Saved sessions:"))
        layoutV1.addWidget(self.treeServerManager)
        layoutV1.addLayout(layoutH4)

        layoutH1 = QHBoxLayout()
        layoutH1.addLayout(layoutV1)

        # Layout for the open/cancel buttons under the tab widget
        layoutH5 = QHBoxLayout()
        layoutH5.addStretch(1)
        layoutH5.addWidget(self.buttonOpen)
        layoutH5.addWidget(buttonCancel)

        self.layoutV2 = QVBoxLayout()
        # layoutV2.addWidget(tabWidget)
        self.layoutV2.addSpacing(17)
        self.layoutV2.addWidget(self.labelNoSession)
        self.layoutV2.addStretch(1)
        self.layoutV2.addLayout(layoutH5)

        # Layout to separate the session manager and tab widget panes
        layoutH3 = QHBoxLayout(self)
        layoutH3.addLayout(layoutH1)
        layoutH3.addLayout(self.layoutV2)
        layoutH3.setStretch(0, 30)
        layoutH3.setStretch(1, 70)

        # Setup signals
        buttonNew.clicked.connect(self.slotButtonNewClicked)
        buttonCancel.clicked.connect(self.slotButtonCancelClicked)
        self.buttonDelete.clicked.connect(self.slotButtonDeleteClicked)
        self.buttonOpen.clicked.connect(self.slotButtonOpenClicked)
        self.buttonSave.clicked.connect(self.slotButtonSaveClicked)
        self.textHostname.textEdited.connect(self.sessionModified)
        self.textUser.textEdited.connect(self.sessionModified)
        self.textPassword.textEdited.connect(self.sessionModified)
        self.spinPort.valueChanged.connect(self.sessionModified)

        self.setLayout(layoutH3)

        self.setWindowTitle("Session manager")
        self.setWindowIcon(QIcon("../resources/icons/heidi.ico"))
        self.setModal(True)
        self.setGeometry(300, 300, 700, 400)

    def addNewServer(self):
        # Add new server to tree view
        newServer = QTreeWidgetItem()
        newServer.setText(0, "Unnamed")
        newServer.setIcon(0, QIcon("../resources/icons/server_add.png"))
        newServer.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.sessionIds.append(None)
        self.treeServerManager.addTopLevelItem(newServer)
        self.treeServerManager.setCurrentItem(newServer)

    def loadSettings(self):
        index = self.treeServerManager.indexOfTopLevelItem(
            self.treeServerManager.currentItem()
        )

        if self.sessionIds[index] is None:
            pass
        else:
            self.curs = self.conn.execute(
                "SELECT * FROM sessions WHERE id = ?", [self.sessionIds[index]]
            )
            settings = self.curs.fetchone()
            self.currentSessionData = settings

            if settings != None:
                self.textHostname.setText(settings["hostname"])
                self.textUser.setText(settings["username"])
                self.textPassword.setText(settings["password"])
                self.spinPort.setValue(settings["port"])
            else:
                self.textHostname.setText("127.0.0.1")
                self.textPassword.setText("")
                self.textUser.setText("root")
                self.spinPort.setValue(3306)

    # Populates the session manager list
    def loadSessionManager(self):
        try:
            self.curs = self.conn.execute("SELECT id, name FROM sessions")

            for row in self.curs:
                newServer = QTreeWidgetItem()
                newServer.setText(0, row["name"])
                newServer.setIcon(0, QIcon("../resources/icons/server.png"))
                newServer.setFlags(
                    Qt.ItemIsEditable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                )

                self.treeServerManager.addTopLevelItem(newServer)
                self.sessionIds.append(row["id"])
            pass

        except OperationalError:
            self.curs = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE Type='table' and name = 'sessions'"
            )

            if self.curs.fetchone() == None:
                self.curs.execute(
                    """
					CREATE TABLE sessions(
					   id INTEGER PRIMARY KEY,
					   name TEXT,
					   network_type INTEGER,
					   hostname TEXT,
					   username TEXT,
					   password TEXT,
					   port INTEGER,
					   compressed BOOL,
					   startup_script TEXT
					);
				"""
                )
            pass

        self.toggleSettingsPane()

    # Called whenever a session setting is modified
    # TODO: Look into a way to remove the asterisk when user edits an item
    def sessionModified(self):
        session = self.treeServerManager.currentItem()

        name = session.text(0)
        if name[-2:] == " *":
            name = name[: len(name) - 2]

        # Check to see if session has been reverted back to normal or not to determine if we need to change the name
        changed = False
        if self.currentSessionData is not None:
            print(self.currentSessionData)
            if self.currentSessionData['hostname'] is not None:
                if (
                    self.textHostname.text() != self.currentSessionData["hostname"]
                    or self.textPassword.text()
                    != self.currentSessionData["password"]
                    or self.textUser.text() != self.currentSessionData["username"]
                    or self.spinPort.value() != self.currentSessionData["port"]
                ):
                    changed = True
                else:
                    changed = False

        if changed == True:
            session.setText(0, name + " *")
            self.buttonSave.setEnabled(True)
            session.setIcon(0, QIcon("../resources/icons/server_edit.png"))
        else:
            session.setText(0, name)
            self.buttonSave.setEnabled(False)
            session.setIcon(0, QIcon("../resources/icons/server.png"))

    def shutdownEvent(self):
        self.conn.commit()
        self.conn.close()

    def slotButtonCancelClicked(self):
        sys.exit(0)

    def slotButtonDeleteClicked(self):
        currentServer = self.treeServerManager.currentItem()
        numServers = self.treeServerManager.topLevelItemCount()

        # Loop through server manager tree until we find the right server, then delete
        for i in range(0, numServers):
            if self.treeServerManager.topLevelItem(i) == currentServer:
                sessionId = self.sessionIds.pop(i)
                self.treeServerManager.takeTopLevelItem(i)
                self.curs.execute("DELETE FROM sessions WHERE id = ?", [sessionId])
                break

        if numServers == 1:
            self.toggleSettingsPane()

    def slotButtonNewClicked(self):
        self.addNewServer()
        self.toggleSettingsPane()

    def slotButtonOpenClicked(self):
        print("open")

    def slotButtonSaveClicked(self):
        index = self.treeServerManager.indexOfTopLevelItem(
            self.treeServerManager.currentItem()
        )
        session = self.treeServerManager.currentItem()
        sessionName = self.treeServerManager.currentItem().text(0)

        if sessionName[-1] == "*":
            sessionName = sessionName[: len(sessionName) - 2]

        if self.sessionIds[index] == None:
            self.curs = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE Type='table' and name = 'sessions'"
            )

            if self.curs.fetchone() == None:
                self.curs.execute(
                    """
					CREATE TABLE sessions(
					   id INTEGER PRIMARY KEY,
					   name TEXT,
					   network_type INTEGER,
					   hostname TEXT,
					   username TEXT,
					   password TEXT,
					   port INTEGER,
					   compressed BOOL,
					   startup_script TEXT
					);
				"""
                )

            self.curs.execute(
                "INSERT INTO sessions (name, network_type, hostname, username, password, port) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    sessionName,
                    self.comboNetworkType.currentIndex(),
                    self.textHostname.text(),
                    self.textUser.text(),
                    self.textPassword.text(),
                    self.spinPort.value(),
                ],
            )
        else:
            self.curs.execute(
                "UPDATE sessions SET name = ?, network_type = ?, hostname = ?, username = ?, password = ?, port = ? WHERE id = ?",
                [
                    sessionName,
                    self.comboNetworkType.currentIndex(),
                    self.textHostname.text(),
                    self.textUser.text(),
                    self.textPassword.text(),
                    self.spinPort.value(),
                    self.sessionIds[index],
                ],
            )

        self.buttonSave.setEnabled(False)
        session.setText(0, sessionName)
        # Set server icon to unedited
        session.setIcon(0, QIcon("../resources/icons/server.png"))

    def slotServerSelectionChanged(self):
        self.loadSettings()

    def toggleSettingsPane(self):
        if self.treeServerManager.topLevelItemCount() > 0:
            # Toggle settings window on
            self.labelNoSession.setVisible(False)
            self.layoutV2.removeItem(self.layoutV2.itemAt(0))
            self.layoutV2.removeItem(self.layoutV2.itemAt(1))
            self.layoutV2.removeWidget(self.labelNoSession)
            self.layoutV2.insertWidget(0, self.tabWidget)
            self.layoutV2.setStretch(1, 1)
            self.tabWidget.setVisible(True)
            self.buttonDelete.setEnabled(True)
            self.buttonOpen.setEnabled(True)
            self.buttonSave.setEnabled(True)
        else:
            # Toggle settings window off and show the no sessions message
            self.labelNoSession.setVisible(True)
            self.layoutV2.removeWidget(self.tabWidget)
            self.layoutV2.insertSpacing(0, 17)
            self.layoutV2.insertWidget(1, self.labelNoSession)
            self.layoutV2.insertStretch(2, 1)
            self.tabWidget.setVisible(False)
            self.buttonDelete.setEnabled(False)
            self.buttonOpen.setEnabled(False)
            self.buttonSave.setEnabled(False)
