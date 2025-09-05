import os
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
    QProgressBar, QFrame
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.downloader import Downloader
from core.clipper import Clipper
from utils.helpers import seconds_to_hms, hms_to_seconds, sanitize_filename


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(dict)
    
    def __init__(self, url, output_dir, start_time, end_time, output_format, video_title):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.start_time = start_time
        self.end_time = end_time
        self.output_format = output_format
        self.video_title = video_title
        
        self.downloader = Downloader(progress_hook=self.handle_progress)
        self.clipper = Clipper()
        self.downloaded_filepath = None

    def run(self):
        """Starts the download and clip process."""
        self.progress.emit({'status': 'info', 'message': 'Starting download...'})
        self.downloader.download_video(self.url, self.output_dir)

    def handle_progress(self, d):
        if d['status'] == 'downloading':
            self.progress.emit(d)
        elif d['status'] == 'finished_download':
            self.downloaded_filepath = d.get('filepath')
            self.progress.emit({'status': 'info', 'message': 'Download complete. Starting clip...'})
            
            safe_title = sanitize_filename(self.video_title)
            clip_filename = f"{safe_title}_{self.start_time.replace(':', '')}_{self.end_time.replace(':', '')}.{self.output_format.lower()}"
            output_filepath = os.path.join(self.output_dir, clip_filename)
            
            self.clipper.clip(
                self.downloaded_filepath,
                output_filepath,
                self.start_time,
                self.end_time,
                self.output_format,
                self.handle_clipping_progress
            )
        elif d['status'] == 'error':
            self.progress.emit(d)
            self.finished.emit()

    def handle_clipping_progress(self, d):
        self.progress.emit(d)
        if d['status'] in ['finished', 'error']:
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'
        self.video_info = None
        self.worker_thread = None
        self.worker = None

        self.setWindowTitle("YouTube Clipper")
        self.setGeometry(100, 100, 600, 700)
        self.set_theme(self.current_theme)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.init_ui()

    def init_ui(self):
        title = QLabel("YouTube Clipper")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("TitleLabel")
        self.main_layout.addWidget(title)

        url_layout = QHBoxLayout()
        self.url_input = self.create_line_edit("Enter YouTube URL...")
        self.fetch_button = self.create_button("Fetch Video", self.fetch_video_info)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.fetch_button)
        self.main_layout.addLayout(url_layout)

        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoFrame")
        self.info_frame.setLayout(QVBoxLayout())
        self.info_frame.setVisible(False)
        self.video_title_label = QLabel("Video Title")
        self.video_title_label.setWordWrap(True)
        self.video_duration_label = QLabel("Duration: 00:00:00")
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(240, 135)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.info_frame.layout().addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)
        self.info_frame.layout().addWidget(self.video_title_label)
        self.info_frame.layout().addWidget(self.video_duration_label)
        self.main_layout.addWidget(self.info_frame)
        
        options_layout = QHBoxLayout()
        options_layout.setSpacing(10)
        
        self.start_time_input = self.create_line_edit("Start (HH:MM:SS)")
        self.start_time_input.setInputMask("99:99:99")
        self.end_time_input = self.create_line_edit("End (HH:MM:SS)")
        self.end_time_input.setInputMask("99:99:99")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "MP3", "GIF"])
        self.format_combo.setObjectName("ComboBox")

        options_layout.addWidget(self.start_time_input)
        options_layout.addWidget(self.end_time_input)
        options_layout.addWidget(self.format_combo)
        self.main_layout.addLayout(options_layout)

        output_layout = QHBoxLayout()
        self.output_path_input = self.create_line_edit("Select Output Folder...")
        self.output_path_input.setReadOnly(True)
        self.browse_button = self.create_button("Browse", self.browse_folder)
        output_layout.addWidget(self.output_path_input)
        output_layout.addWidget(self.browse_button)
        self.main_layout.addLayout(output_layout)

        self.clip_button = self.create_button("Clip Video", self.start_clipping, is_primary=True)
        self.clip_button.setEnabled(False)
        self.main_layout.addWidget(self.clip_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Welcome!")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.main_layout.addWidget(self.status_label)
        
        self.main_layout.addStretch()

        self.theme_button = QPushButton("Toggle Theme")
        self.theme_button.setCheckable(True)
        self.theme_button.setChecked(self.current_theme == 'dark')
        self.theme_button.toggled.connect(self.toggle_theme)
        self.theme_button.setObjectName("ThemeButton")
        self.main_layout.addWidget(self.theme_button, alignment=Qt.AlignCenter)

    def create_line_edit(self, placeholder):
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setObjectName("LineEdit")
        return line_edit

    def create_button(self, text, on_click, is_primary=False):
        button = QPushButton(text)
        button.clicked.connect(on_click)
        button.setObjectName("PrimaryButton" if is_primary else "Button")
        return button

    def fetch_video_info(self):
        url = self.url_input.text()
        if not url:
            self.set_status("Please enter a YouTube URL.", "error")
            return
        
        self.set_status("Fetching video information...", "info")
        self.fetch_button.setEnabled(False)
        
        downloader = Downloader()
        self.video_info = downloader.fetch_video_info(url)
        
        self.fetch_button.setEnabled(True)

        if self.video_info:
            self.info_frame.setVisible(True)
            self.video_title_label.setText(self.video_info['title'])
            duration_hms = seconds_to_hms(self.video_info['duration'])
            self.video_duration_label.setText(f"Duration: {duration_hms}")
            self.end_time_input.setText(duration_hms)
            self.start_time_input.setText("00:00:00")
            
            if self.video_info['thumbnail_url']:
                try:
                    data = requests.get(self.video_info['thumbnail_url']).content
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    self.thumbnail_label.setPixmap(pixmap)
                except Exception as e:
                    self.thumbnail_label.setText("No Thumbnail")
            
            self.clip_button.setEnabled(True)
            self.set_status("Video info fetched successfully.", "success")
        else:
            self.info_frame.setVisible(False)
            self.clip_button.setEnabled(False)
            self.set_status("Failed to fetch video info. Check URL and connection.", "error")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.output_path_input.setText(folder)

    def start_clipping(self):
        if not self.video_info or not self.output_path_input.text():
            self.set_status("Fetch info and select an output folder first.", "error")
            return
        
        start_sec = hms_to_seconds(self.start_time_input.text())
        end_sec = hms_to_seconds(self.end_time_input.text())
        
        if start_sec >= end_sec or end_sec > self.video_info['duration']:
            self.set_status("Invalid start/end time.", "error")
            return

        self.clip_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker_thread = QThread()
        self.worker = Worker(
            url=self.url_input.text(),
            output_dir=self.output_path_input.text(),
            start_time=self.start_time_input.text(),
            end_time=self.end_time_input.text(),
            output_format=self.format_combo.currentText(),
            video_title=self.video_info['title']
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker_thread.start()

    def update_progress(self, data):
        status = data.get('status')
        if status == 'downloading':
            self.set_status("Downloading video...", "info")
            self.progress_bar.setValue(int(data.get('percent', 0)))
        elif status == 'clipping':
            self.set_status(data.get('message', 'Clipping...'), "info")
            self.progress_bar.setRange(0, 0)
        elif status == 'finished':
            self.set_status(data.get('message'), "success")
        elif status == 'error':
            self.set_status(data.get('message') or data.get('error'), "error")
        elif status == 'info':
            self.set_status(data.get('message'), "info")

    def on_worker_finished(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.clip_button.setEnabled(True)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker_thread = None
        self.worker = None

    def set_status(self, message, level="info"):
        self.status_label.setText(message)
        if level == "success":
            self.status_label.setStyleSheet("color: #34D399;")
        elif level == "error":
            self.status_label.setStyleSheet("color: #F87171;")
        else:
            self.status_label.setStyleSheet(f"color: {'#9CA3AF' if self.current_theme == 'dark' else '#4B5563'};")

    def toggle_theme(self, checked):
        self.current_theme = 'dark' if checked else 'light'
        self.set_theme(self.current_theme)

    def set_theme(self, theme_name):
        self.set_status(self.status_label.text())
        if theme_name == 'dark':
            self.setStyleSheet(self.get_dark_theme_stylesheet())
        else:
            self.setStyleSheet(self.get_light_theme_stylesheet())

    def get_dark_theme_stylesheet(self):
        return """
            QWidget { background-color: #1F2937; color: #F9FAFB; }
            #TitleLabel { color: #FFFFFF; }
            #LineEdit, #ComboBox { background-color: #374151; border: 1px solid #4B5563; border-radius: 8px; padding: 10px; font-size: 14px; }
            #LineEdit:focus { border: 1px solid #3B82F6; }
            #Button, #ThemeButton { background-color: #4B5563; border: none; border-radius: 8px; padding: 10px 15px; font-size: 14px; font-weight: bold; }
            #Button:hover { background-color: #6B7280; }
            #PrimaryButton { background-color: #3B82F6; color: #FFFFFF; }
            #PrimaryButton:hover { background-color: #60A5FA; }
            #PrimaryButton:disabled { background-color: #4B5563; color: #9CA3AF; }
            #ThemeButton[checked=true] { background-color: #3B82F6; }
            #InfoFrame { background-color: #374151; border-radius: 8px; padding: 15px; }
            QProgressBar { border: 1px solid #4B5563; border-radius: 8px; text-align: center; background-color: #374151; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 7px; }
        """

    def get_light_theme_stylesheet(self):
        return """
            QWidget { background-color: #F3F4F6; color: #111827; }
            #TitleLabel { color: #111827; }
            #LineEdit, #ComboBox { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 8px; padding: 10px; font-size: 14px; }
            #LineEdit:focus { border: 1px solid #3B82F6; }
            #Button, #ThemeButton { background-color: #E5E7EB; border: none; border-radius: 8px; padding: 10px 15px; font-size: 14px; font-weight: bold; }
            #Button:hover { background-color: #D1D5DB; }
            #PrimaryButton { background-color: #3B82F6; color: #FFFFFF; }
            #PrimaryButton:hover { background-color: #60A5FA; }
            #PrimaryButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
            #ThemeButton[checked=false] { background-color: #D1D5DB; }
            #InfoFrame { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 15px; }
            QProgressBar { border: 1px solid #D1D5DB; border-radius: 8px; text-align: center; background-color: #E5E7EB; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 7px; }
        """

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            if self.worker and hasattr(self.worker, 'downloader'):
                self.worker.downloader.cancel_download()
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()