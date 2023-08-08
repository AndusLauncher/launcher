import os
import shutil
import subprocess
import sys
import json
import urllib.request
import zipfile

import feedparser
import semver
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, \
    QPushButton, QFrame, QProgressDialog, QMessageBox, QLineEdit, QMenu, QApplication, QDialog, QTextBrowser
from PyQt5.QtGui import QFont, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QUrl
from qt_material import apply_stylesheet
from src.customs.custom_title_bar import CustomTitleBar


class GameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Andus Launcher")
        self.setGeometry(100, 100, 1100, 700)
        self.setWindowFlag(Qt.FramelessWindowHint)
        apply_stylesheet(self, theme='dark_blue.xml')

        self.title_bar = CustomTitleBar(self)
        self.setMenuWidget(self.title_bar)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.setup_ui()

    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setup_game_list_and_search()
        self.setup_details_frame()

        self.load_game_list()
        self.original_working_directory = os.getcwd()
        self.center_on_screen()

    def setup_game_list_and_search(self):
        self.game_list_and_search_layout = QVBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setFont(QFont("Roboto", 14))
        self.search_bar.setPlaceholderText("Search by Game or Developer")
        self.search_bar.textChanged.connect(self.filter_game_list)
        self.game_list_and_search_layout.addWidget(self.search_bar)

        self.game_list_widget = QListWidget()
        self.game_list_widget.setFont(QFont("Roboto", 14))
        self.game_list_and_search_layout.addWidget(self.game_list_widget)

        self.layout.addLayout(self.game_list_and_search_layout)

    def setup_details_frame(self):
        self.details_frame = QFrame()
        self.details_frame.setFrameShape(QFrame.StyledPanel)
        self.details_layout = QVBoxLayout(self.details_frame)

        self.options_button = QPushButton("...")
        self.options_button.setFont(QFont("Roboto", 14))
        self.options_button.setFixedHeight(40)
        self.options_button.setFixedWidth(40)
        self.options_menu = QMenu(self)
        self.uninstall_action = self.options_menu.addAction("Uninstall")
        self.open_directory_action = self.options_menu.addAction("Open Game Directory")
        self.open_game_website_action = self.options_menu.addAction("Open Website")
        self.updates_action = self.options_menu.addAction("Updates")
        self.options_button.setMenu(self.options_menu)
        self.details_layout.addWidget(self.options_button, alignment=Qt.AlignRight)
        self.uninstall_action.triggered.connect(self.uninstall_game)
        self.open_directory_action.triggered.connect(self.open_game_directory)
        self.open_game_website_action.triggered.connect(self.open_game_website)
        self.updates_action.triggered.connect(self.open_updates_rss_reader)
        self.options_button.setVisible(False)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(150, 150)
        self.details_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        self.name_and_developer_layout = QVBoxLayout()
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font: bold 24px 'Roboto'; qproperty-alignment: AlignCenter;")
        self.name_and_developer_layout.addWidget(self.name_label, alignment=Qt.AlignCenter)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font: 12px 'Roboto'; qproperty-alignment: AlignCenter;")
        self.name_and_developer_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        self.developer_label = QLabel()
        self.developer_label.setStyleSheet("font: 16px 'Roboto'; qproperty-alignment: AlignCenter;")
        self.name_and_developer_layout.addWidget(self.developer_label, alignment=Qt.AlignCenter)

        self.details_layout.addLayout(self.name_and_developer_layout)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font: 16px 'Roboto';")
        self.details_layout.addWidget(self.description_label)

        self.play_button = QPushButton("Play")
        self.play_button.setFont(QFont("Roboto", 14))
        self.play_button.clicked.connect(self.play_game)
        self.play_button.setFixedHeight(40)
        self.details_layout.addWidget(self.play_button, alignment=Qt.AlignCenter)
        self.play_button.setVisible(False)

        self.layout.addWidget(self.details_frame, 2)
        self.options_button.setVisible(False)

    def load_game_list(self):
        try:
            url = "https://raw.githubusercontent.com/anduslauncher/gamelist/master/games.json"
            response = urllib.request.urlopen(url)
            data = json.load(response)
            with open("games.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
            self.load_game_list_from_data(data)
        except urllib.error.URLError as e:
            print("Error loading game list online:", e)
            try:
                with open("games.json", "r") as json_file:
                    data = json.load(json_file)
                    self.load_game_list_from_data(data)
            except FileNotFoundError:
                print("Local game list not found")

    def load_game_list_from_data(self, data):
        self.game_list_widget.clear()
        self.games = data["games"]
        for game in self.games:
            game_item = QListWidgetItem(game["name"])
            self.game_list_widget.addItem(game_item)

            icon_url = game["icon"]
            icon_path = os.path.join("icons", f"{game['ID']}.png")
            if not os.path.exists(icon_path):
                self.download_icon(icon_url, "icons", str(game['ID']))
            icon = QIcon(icon_path)
            game_item.setIcon(icon)
        self.game_list_widget.itemClicked.connect(self.update_game_details)

    def filter_game_list(self, filter_text):
        filter_text = filter_text.lower()
        self.game_list_widget.clear()
        for game in self.games:
            if filter_text in game["name"].lower() or filter_text in game["developer"].lower():
                game_item = QListWidgetItem(game["name"])
                self.game_list_widget.addItem(game_item)
                icon_url = game["icon"]
                icon_path = os.path.join("icons", f"{game['ID']}.png")
                if not os.path.exists(icon_path):
                    self.download_icon(icon_url, "icons", str(game['ID']))
                icon = QIcon(icon_path)
                game_item.setIcon(icon)
        self.game_list_widget.setCurrentRow(0)

    def update_game_details(self, item):
        selected_game = item.text()
        game_info = next((game for game in self.games if game["name"] == selected_game), None)
        if game_info:
            self.name_label.setText(game_info["name"])
            self.developer_label.setText(game_info["developer"])
            self.status_label.setText("Status: " + game_info["devstatus"])
            self.description_label.setText("Description: " + game_info["description"])
            icon_path = os.path.join("icons", f"{game_info['ID']}.png")
            icon = QIcon(icon_path)
            original_pixmap = icon.pixmap(128, 128)
            scaled_pixmap = original_pixmap.scaled(QSize(150, 150), Qt.KeepAspectRatio)
            self.icon_label.setPixmap(scaled_pixmap)
            self.selected_game_info = game_info
            installed_version = self.get_installed_version(game_info["ID"])
            latest_version = game_info.get("version", "0.0.0")

            version_comparison = semver.compare(installed_version, latest_version)
            if os.path.exists(os.path.join("games", str(game_info["ID"]))):
                if version_comparison < 0:
                    self.play_button.setText("Update")
                    self.play_button.setStyleSheet("background-color: #CC9900; color: white; border: 2px solid "
                                                   "#A97D00;")
                else:
                    self.play_button.setText("Play")
                    self.play_button.setStyleSheet("background-color: #00A859; color: white; border: 2px solid #006B3C;")
            else:
                self.play_button.setText("Download")
                self.play_button.setStyleSheet("background-color: #008F9F; color: white;")
            if "website" in game_info:
                self.open_game_website_action.setVisible(True)
            else:
                self.open_game_website_action.setVisible(False)
            if 'rss_feed' in game_info:
                self.updates_action.setVisible(True)
            else:
                self.updates_action.setVisible(False)
            self.play_button.setVisible(True)
            self.options_button.setVisible(True)

    def get_installed_version(self, game_id):
        game_folder = os.path.join("games", str(game_id))
        version_file_path = os.path.join(game_folder, "installed_version.alauncher")
        if os.path.exists(version_file_path):
            with open(version_file_path, "r") as version_file:
                return version_file.read().strip()
        return "0.0.0"

    def download_game(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            platform = "win" if sys.platform == "win32" else "linux"
            download_link_key = f"download_link_{platform}"
            if download_link_key in game_info:
                download_url = game_info[download_link_key]
                download_folder = "games"

                if not os.path.exists(download_folder):
                    os.makedirs(download_folder)
                game_id = game_info["ID"]
                game_folder = os.path.join(download_folder, str(game_id))
                game_file_name = os.path.basename(download_url)
                game_file_path = os.path.join(game_folder, game_file_name)

                if not os.path.exists(game_file_path):
                    self.show_progress_dialog("Downloading", "Downloading the game...", self.download_game_file,
                                              download_url, game_file_path)
                else:
                    self.show_progress_dialog("Extracting", "Extracting the game...", self.extract_game, game_file_path,
                                              game_folder)

    def download_game_file(self, url, local_path):
        def report_hook(count, block_size, total_size):
            if self.progress_dialog is not None:
                percentage = int(count * block_size * 100 / total_size)
                self.progress_dialog.setValue(percentage)

        print("Downloading from:", url)
        print("Saving to:", local_path)

        if not os.path.exists(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))

        urllib.request.urlretrieve(url, local_path, report_hook)
        self.progress_dialog.close()
        self.save_installed_version(os.path.dirname(local_path), self.selected_game_info["version"])
        self.update_local_games_json()

        if local_path.endswith(".zip"):
            game_folder = os.path.dirname(local_path)
            self.show_progress_dialog("Extracting", "Extracting the game...", self.extract_game, local_path, game_folder)
        else:
            self.play_button.setText("Play")
            self.update_game_details(self.game_list_widget.currentItem())

    def extract_game(self, zip_file_path, extraction_path):
        print("Extracting the game")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            total_files = len(zip_ref.infolist())
            extracted_files = 0
            for item in zip_ref.infolist():
                extracted_files += 1
                percentage = int(extracted_files * 100 / total_files)
                self.progress_dialog.setValue(percentage)
                zip_ref.extract(item, extraction_path)
            os.remove(zip_file_path)
            self.progress_dialog.close()
            self.play_button.setText("Play")
            self.update_game_details(self.game_list_widget.currentItem())

    def show_progress_dialog(self, title, label, callback, *args):
        self.progress_dialog = QProgressDialog(label, "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        self.progress_dialog.canceled.connect(self.progress_dialog.close)
        callback(*args)

    def save_installed_version(self, game_folder, version):
        version_file_path = os.path.join(game_folder, "installed_version.alauncher")
        with open(version_file_path, "w") as version_file:
            version_file.write(version)

    def update_local_games_json(self):
        try:
            url = "https://raw.githubusercontent.com/anduslauncher/gamelist/master/games.json"
            response = urllib.request.urlopen(url)
            new_data = json.load(response)
            with open("games.json", "r+") as json_file:
                current_data = json.load(json_file)
                json_file.seek(0)
                json.dump(new_data, json_file, indent=4)
                json_file.truncate()
                self.games = new_data["games"]
        except urllib.error.URLError as e:
            print("Error updating local game list:", e)

    def download_icon(self, url, folder, game_id):
        icon_path = os.path.join(folder, f"{game_id}.png")
        if os.path.exists(icon_path):
            print(f"Icon {game_id}.png already exists, not downloading")
            return
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
            response = urllib.request.urlopen(url)
            icon_data = response.read()
            with open(icon_path, "wb") as icon_file:
                icon_file.write(icon_data)
        except Exception as e:
            print("Error downloading icon:", e)

    def play_game(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            platform = "win" if sys.platform == "win32" else "linux"
            executable_key = f"exec_{platform}"

            installed_version = self.get_installed_version(game_info["ID"])
            latest_version = game_info.get("version", "0.0.0")

            if installed_version == latest_version:
                if executable_key in game_info:
                    executable = game_info[executable_key]
                    game_id = game_info["ID"]
                    game_folder = os.path.join("games", str(game_id))
                    executable_path = os.path.join(game_folder, executable)

                    if os.path.exists(executable_path):
                        if platform == "linux":
                            os.chmod(executable_path, 0o755)
                        subprocess.Popen([executable_path], shell=True)
                    else:
                        print(f"Executable '{executable}' not found in '{game_folder}'.")
                        print("Attempting to download the game.")
                        self.download_game()
            else:
                self.download_game()

    def uninstall_game(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            game_id = game_info["ID"]
            game_folder = os.path.join("games", str(game_id))
            if os.path.exists(game_folder):
                self.show_uninstall_confirmation(game_folder)

    def show_uninstall_confirmation(self, game_folder):
        response = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall the game?\nThis will delete the game folder '{game_folder}' of game '{self.selected_game_info['name']}'.",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.Yes:
            try:
                shutil.rmtree(game_folder)
                print(f"Game uninstalled: {game_folder}")
                self.update_game_details(self.game_list_widget.currentItem())
            except Exception as e:
                print("Error uninstalling game:", e)

    def open_game_directory(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            game_id = game_info["ID"]
            game_folder = os.path.join("games", str(game_id))
            if os.path.exists(game_folder):
                try:
                    os.system(f"xdg-open '{game_folder}'")
                except Exception as e:
                    print("Error opening game directory:", e)

    def open_game_website(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            if "website" in game_info:
                website_url = game_info["website"]
                try:
                    os.system(f"xdg-open '{website_url}'")
                except Exception as e:
                    print("Error opening the website:", e)

    def open_updates_rss_reader(self):
        if hasattr(self, 'selected_game_info'):
            game_info = self.selected_game_info
            if 'rss_feed' in game_info:
                rss_feed_url = game_info['rss_feed']
                game_name = game_info['name']
                rss_reader_window = RSSReaderWindow(game_name)
                rss_reader_window.load_feed(rss_feed_url, game_name)
                rss_reader_window.exec_()

    def close_button_clicked(self):
        self.close()

    def center_on_screen(self):
        screen_geometry = QApplication.desktop().screenGeometry()

        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        self.move(x, y)

    def unzip_game(self, zip_file, destination):
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(destination)
        print(f"{os.path.basename(zip_file)} unzipped to {destination}")

    def save_installed_version(self, game_folder, version):
        version_file_path = os.path.join(game_folder, "installed_version.alauncher")
        with open(version_file_path, "w") as version_file:
            version_file.write(version)


class RSSReaderWindow(QDialog):
    def __init__(self, game_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{game_name} - Updates")
        self.setGeometry(200, 200, 800, 600)

        self.layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.anchorClicked.connect(self.handle_link_click)
        self.layout.addWidget(self.text_browser)

    def load_feed(self, feed_url, game_name):
        feed = feedparser.parse(feed_url)

        html_content = "<style>a { color: #007bff; text-decoration: none; }</style>"
        html_content += f"<h1>{game_name} Updates</h1>"

        for entry in feed.entries:
            title = entry.title
            published_date = entry.published
            link = entry.link
            summary = entry.summary

            html_content += f"<h2><a href='{link}'>{title}</a></h2>"
            html_content += f"<p><em>{published_date}</em></p>"
            html_content += f"<p>{summary}</p>"
            html_content += "<hr>"

        self.text_browser.setHtml(html_content)

    def handle_link_click(self, link):
        url = link.toString()
        if url.startswith("http://") or url.startswith("https://"):
            os.system(f"xdg-open '{url}'")

