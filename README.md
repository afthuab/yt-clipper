# YouTube Clipper

A simple yet powerful desktop application for Windows to download and trim clips from YouTube videos.



## ✨ Features

* **Easy Clipping**: Paste a YouTube URL, set the start and end times, and get your clip.
* **Multiple Formats**: Export clips as high-quality **MP4**, audio-only **MP3**, or animated **GIF**.
* **Metadata Fetching**: Automatically fetches the video title, duration, and thumbnail.
* **Modern UI**: A clean, user-friendly interface with a switchable **Dark Mode**.
* **Real-time Progress**: A progress bar keeps you updated on the download and clipping process.

---

## 💻 Tech Stack

* **Language**: Python
* **GUI Framework**: PyQt5
* **Video Downloading**: `yt-dlp`
* **Video Processing**: `FFmpeg`
* **Packaging**: PyInstaller

---

## 🛠️ Prerequisites

Before you begin, you must have **FFmpeg** installed and added to your system's PATH.

1.  **Download FFmpeg**: Get a static build from the [official FFmpeg website](https://ffmpeg.org/download.html).
2.  **Add to PATH**: Unzip the file and add the location of the `bin` folder (e.g., `C:\ffmpeg\bin`) to your system's PATH environment variable.
3.  **Verify**: Open a new Command Prompt and run `ffmpeg -version`. You should see version information if it's installed correctly.

---

## ⚙️ Setup and Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/afthuab/yt-clipper.git

    cd youtube-clipper
    ```


2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

---

## Usage Guide

1.  **Paste URL**: Paste a YouTube video URL and click **"Fetch Video"**.
2.  **Set Times**: Enter the desired **Start Time** and **End Time** in `HH:MM:SS` format.
3.  **Choose Format**: Select your output format (MP4, MP3, or GIF) from the dropdown.
4.  **Select Folder**: Click **"Browse"** to choose where to save your clip.
5.  **Clip Video**: Click the **"Clip Video"** button and wait for the process to complete!

---

## 📦 Building the Executable

To create a standalone `.exe` file that can be shared and run on other Windows computers without needing Python installed:

```bash
pyinstaller build.spec