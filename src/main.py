import sys

from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QApplication
from launcher import GameLauncher

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    launcher = GameLauncher()
    launcher.network_manager = QNetworkAccessManager()
    launcher.update_local_games_json()
    launcher.show()
    sys.exit(app.exec_())
