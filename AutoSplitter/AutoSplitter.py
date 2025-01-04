import subprocess
import sys
import ensurepip

# --- Dependency Management ---
REQUIRED_PACKAGES = ['opencv-python', 'numpy', 'pyautogui', 'keyboard', 'pillow']

def ensure_pip():
    """Ensure pip is installed."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', '--version'])
    except subprocess.CalledProcessError:
        print("pip not found. Installing pip...")
        ensurepip.bootstrap()
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

def install_missing_packages():
    """Check and install missing dependencies."""
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Ensure pip and dependencies are installed
ensure_pip()
install_missing_packages()

# --- Main Script ---
import socket
import cv2
import numpy as np
import pyautogui
import time
import keyboard

# Reference images
start_reference = cv2.imread('start.png', 0)
split_reference = cv2.imread('split.png', 0)
end_reference = cv2.imread('end.png', 0)
reset_reference = cv2.imread('reset.png', 0)

if start_reference is None:
    print("Error: 'start.png' not found!")
    exit()
if split_reference is None:
    print("Error: 'split.png' not found!")
    exit()
if end_reference is None:
    print("Error: 'end.png' not found!")
    exit()
if reset_reference is None:
    print("Error: 'reset.png' not found!")
    exit()

# Detection threshold and settings
THRESHOLD = 0.8
COOLDOWN = 2
STATE = "IDLE"
LIVESPLIT_TCP_PORT = 16834

def trigger_action(action: str):
    """Send commands to LiveSplit TCP Server."""
    actions = {
        "start": "starttimer",
        "split": "split",
        "stop": "pause",
        "reset": "reset"
    }
    if action not in actions:
        print("Invalid action!")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", LIVESPLIT_TCP_PORT))
            s.send(f"{actions[action]}\r\n".encode('utf-8'))
            print(f"Command '{actions[action]}' sent successfully!")
    except Exception as e:
        print(f"Failed to send command '{action}': {e}")

def check_detection(reference, label):
    """Check if the reference image is detected on screen."""
    region = (0, 0, 1920, 1080)
    
    screenshot = pyautogui.screenshot(region=region)
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    result = cv2.matchTemplate(screenshot, reference, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    print(f"{label} Detection Confidence: {max_val:.2f}")

    if max_val >= THRESHOLD:
        print(f"{label} cue detected at {max_loc}")
        return True
    return False

# Main Loop
print("Starting detection loop. Press 'Esc' to stop.")
try:
    last_action_time = 0

    while True:
        if keyboard.is_pressed('esc'):
            print("Stopping detection.")
            break

        current_time = time.time()
        if current_time - last_action_time < COOLDOWN:
            time.sleep(0.1)
            continue

        if STATE == "IDLE":
            if check_detection(start_reference, "Start"):
                trigger_action("start")
                STATE = "RUNNING"
                last_action_time = current_time

        elif STATE == "RUNNING":
            if check_detection(split_reference, "Split"):
                trigger_action("split")
                last_action_time = current_time

            if check_detection(end_reference, "End"):
                trigger_action("split")
                STATE = "IDLE"
                last_action_time = current_time

            if check_detection(reset_reference, "Reset"):
                trigger_action("reset")
                STATE = "IDLE"
                print("Timer reset detected!")
                last_action_time = current_time

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Detection manually stopped.")
