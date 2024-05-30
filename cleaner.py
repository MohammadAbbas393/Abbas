"""
Downloads Cleaner

A few lines of code that keep old and unused files away from your Downloads folder forever!

Author:     Mohammad Abbas
Github:     https://github.com/MohammadAbbas393/Downloads-folder-cleaner
College:    Middlebury college
"""
import os
import shutil
import threading
import logging
from PIL import Image, ImageDraw, ImageFilter
from time import time, sleep
from pathlib import Path
import pystray
from pystray import MenuItem as item
import subprocess

# Setup
ICON_SIZE = (32, 32)
ICON_COLOR = (0, 0, 0)  # Black background
TEXT_COLOR = (255, 0, 0)  # Red text
REFRESH_RATE = 60  # seconds
move_file_after_hours = 0.01  # Temporarily set to a very low value for testing

# Determine the path to the user's Downloads directory
downloads_path = str(Path.home() / "Downloads")

# Configurations
destination_file = downloads_path
items_ignore = ["cleaner.log", "config.yaml", "icon.ico"]

running = True
trayicon = None

# Base directories for categories
base_directories = {
    'audio': os.path.join(downloads_path, "Audio"),
    'photos': os.path.join(downloads_path, "Photos"),
    'text': {
        'pdf': os.path.join(downloads_path, "Text/PDF"),
        'word': os.path.join(downloads_path, "Text/Word"),
        'txt': os.path.join(downloads_path, "Text/TXT"),
        'other': os.path.join(downloads_path, "Text/Other")
    },
    'programming': {
        'python': os.path.join(downloads_path, "Programming/Python"),
        'java': os.path.join(downloads_path, "Programming/Java"),
        'c': os.path.join(downloads_path, "Programming/C/C++"),
        'csharp': os.path.join(downloads_path, "Programming/C#"),
        'javascript': os.path.join(downloads_path, "Programming/JavaScript"),
        'data': os.path.join(downloads_path, "Programming/Data"),
        'other': os.path.join(downloads_path, "Programming/Other")
    },
    'uncategorized': os.path.join(downloads_path, "Uncategorized")
}

# Extension to category mapping with detailed subcategories
extension_categories = {
    '.aif': 'audio', '.cda': 'audio', '.mid': 'audio', '.midi': 'audio', '.mp3': 'audio',
    '.mpa': 'audio', '.ogg': 'audio', '.wav': 'audio', '.wma': 'audio', '.wpl': 'audio', '.m3u': 'audio',
    '.jpg': 'photos', '.jpeg': 'photos', '.png': 'photos', '.bmp': 'photos', '.gif': 'photos', '.tif': 'photos', '.tiff': 'photos',
    '.txt': 'text.txt', '.doc': 'text.word', '.docx': 'text.word', '.odt': 'text.other', '.pdf': 'text.pdf',
    '.rtf': 'text.other', '.tex': 'text.other', '.wks': 'text.other', '.wps': 'text.other', '.wpd': 'text.other',
    '.py': 'programming.python', '.java': 'programming.java', '.c': 'programming.c', '.cs': 'programming.csharp',
    '.js': 'programming.javascript', '.html': 'programming.other', '.h': 'programming.other',
    '.csv': 'programming.data', '.xls': 'programming.data', '.xlsx': 'programming.data', '.json': 'programming.data', '.xml': 'programming.data', '.db': 'programming.data',
    'default': 'uncategorized'
}

def ensure_directories():
    """Ensure that all base directories and subdirectories are created."""
    for category, path in base_directories.items():
        if isinstance(path, dict):
            for subcategory, subpath in path.items():
                if not os.path.exists(subpath):
                    os.makedirs(subpath)
                    logging.info(f"Created directory: {subpath}")
        else:
            if not os.path.exists(path):
                os.makedirs(path)
                logging.info(f"Created directory: {path}")

def get_used_time(item):
    """Get the latest timestamp of file access, modification, or creation."""
    return max(os.path.getatime(item), os.path.getctime(item), os.path.getmtime(item))

def notify(message, title="Downloads Cleaner"):
    """Send a notification with given message and title."""
    if trayicon:
        trayicon.notify(message, title=title)
    logging.info(f"{title}: {message}")

def quit_icon():
    """Quit the application."""
    global running
    running = False
    if trayicon:
        trayicon.stop()

def create_placeholder_image():
    """Create a placeholder icon image."""
    image = Image.new('RGB', ICON_SIZE, ICON_COLOR)
    draw = ImageDraw.Draw(image)
    draw.text((8, 8), "MA", fill=TEXT_COLOR)
    return image

def open_downloads():
    """Open the Downloads directory."""
    if os.name == 'posix':  # For macOS and Linux
        subprocess.call(['open', downloads_path])
    elif os.name == 'nt':  # For Windows
        os.startfile(downloads_path)

def trayicon_init():
    """Initialize the system tray icon."""
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        icon = create_placeholder_image()
        icon.save(icon_path)
    else:
        icon = Image.open(icon_path)

    global trayicon
    trayicon = pystray.Icon("Downloads Cleaner", icon, menu=pystray.Menu(
        item('Quit', quit_icon),
        item('Open Downloads', lambda: open_downloads())
    ))
    trayicon.run()

def move_file(original, destination):
    """Move the file to the designated directory."""
    try:
        if not os.path.exists(destination):
            os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.move(original, destination)
        logging.info(f"Moved {original} to {destination}")
    except Exception as e:
        logging.error(f"Failed to move {original} to {destination}: {e}")
        raise

def scan_directory(directory):
    """Scan the directory for files that meet the criteria for moving."""
    moved = False
    for item in os.listdir(directory):
        if item in items_ignore or os.path.isdir(os.path.join(directory, item)):
            continue
        full_path = os.path.join(directory, item)
        last_used = get_used_time(full_path)
        if (time() - last_used) / 3600 >= move_file_after_hours:
            extension = os.path.splitext(item)[1].lower()
            category_key = extension_categories.get(extension, 'uncategorized')
            try:
                if '.' in category_key:
                    category, subcategory = category_key.split('.')
                    base_path = base_directories[category][subcategory]
                else:
                    base_path = base_directories[category_key]
            except KeyError:
                base_path = base_directories['uncategorized']
            destination = os.path.join(base_path, item)
            move_file(full_path, destination)
            moved = True
    return moved

def scan():
    """Scan all directories for old files and move them. Return True if any files were moved."""
    ensure_directories()
    moved_any = False
    for directory in [downloads_path]:
        if scan_directory(directory):
            moved_any = True
            break  # Stop scanning once we know files have been moved
    return moved_any

def loop():
    """Main loop to repeatedly check for old files and quit if no files are moved."""
    notify("Scan started.", "Scan Information")
    while running:
        if not scan():  # If no files were moved in the scan
            notify("No files to move. Quitting application.", "Scan Complete")
            break  # Exit the loop if no files were moved
        sleep(REFRESH_RATE)  # Wait before the next scan cycle
    quit_icon()  # Quit the application once the loop is exited

def thread_function():
    try:
        loop()
    except Exception as e:
        logging.critical("An error occurred in the background thread: {}".format(e))


def main():
    """Main function to set up logging, start the tray icon and the scanning loop."""
    logging.basicConfig(filename="Downloads cleaner.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")  # Includes timestamp
    logging.info("Downloads Cleaner started.")
    ensure_directories()
    thread = threading.Thread(target=thread_function)
    thread.start()
    trayicon_init()
    thread.join()

if __name__ == "__main__":
    main()
