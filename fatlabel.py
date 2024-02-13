"""
@forker: LaminarRainbow 
@title: FATLABEL
@nickname: FATLABEL
@description: A modified fork of FatLabels to add additional input features. 
"""

import torch
import numpy as np
import folder_paths
import sys
import subprocess
import threading
import locale
import pandas as pd
import os

comfy__path = os.path.dirname(folder_paths.__file__)
fatlabel__path = os.path.join(os.path.dirname(__file__))

def handle_stream(stream, is_stdout):
    stream.reconfigure(encoding=locale.getpreferredencoding(), errors='replace')

    for msg in stream:
        if is_stdout:
            print(msg, end="", file=sys.stdout)
        else: 
            print(msg, end="", file=sys.stderr)


def process_wrap(cmd_str, cwd=None, handler=None):
    print(f"🏷️ FATLABEL (execute): {cmd_str} in '{cwd}'")
    process = subprocess.Popen(cmd_str, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    if handler is None:
        handler = handle_stream

    stdout_thread = threading.Thread(target=handler, args=(process.stdout, True))
    stderr_thread = threading.Thread(target=handler, args=(process.stderr, False))

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()

    return process.wait()


pip_list = None


def get_installed_packages():
    global pip_list

    if pip_list is None:
        try:
            result = subprocess.check_output([sys.executable, '-m', 'pip', 'list'], universal_newlines=True)
            pip_list = set([line.split()[0].lower() for line in result.split('\n') if line.strip()])
        except subprocess.CalledProcessError as e:
            print(f"[ComfyUI-Manager] Failed to retrieve the information of installed pip packages.")
            return set()
    
    return pip_list
    

def is_installed(name):
    name = name.strip()
    pattern = r'([^<>!=]+)([<>!=]=?)'
    match = re.search(pattern, name)
    
    if match:
        name = match.group(1)
        
    result = name.lower() in get_installed_packages()
    return result
    

def is_requirements_installed(file_path):
    print(f"req_path: {file_path}")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if not is_installed(line):
                    return False
                    
    return True

print("🏷️ FATLABEL: Check dependencies")

if "python_embeded" in sys.executable or "python_embedded" in sys.executable:
    pip_install = [sys.executable, '-s', '-m', 'pip', 'install']
    mim_install = [sys.executable, '-s', '-m', 'mim', 'install']
else:
    pip_install = [sys.executable, '-m', 'pip', 'install']
    mim_install = [sys.executable, '-m', 'mim', 'install']

try:
    from PIL import Image, ImageDraw, ImageColor, ImageFont
except Exception:
    process_wrap(pip_install + ['Pillow'])

try:
    from freetype import *  # Import freetype-py
except Exception:
    process_wrap(pip_install + ['freetype-py'])

print(f"### Loading: Fat Labels (v0.2.3)")

class BasicFatLabel:
    def __init__(self, device="cpu"):
        self.device = device

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": ""}),
                "font_path": ("STRING", {"default": f"{fatlabel__path}/fonts/Bevan-Regular.ttf", "multiline": False}),
                "font_color_hex": ("STRING", {"default": "#888888", "multiline": False}),
                "background_color_hex": ("STRING", {"default": "#000000", "multiline": False}),
                "font_size": ("INT", {"default": 72, "min": 1}),  # Font size in pixels
                "kerning_value": ("FLOAT", {"default": 0.0}),  # New input for kerning
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "create_basic_fatlabel"
    CATEGORY = "🏷️ FATLABEL (Basic)"

    def create_basic_fatlabel(self, text="", background_color_hex="#000000", font_color_hex="#888888", font_path=f"{fatlabel__path}/fonts/Bevan-Regular.ttf", font_size=72, kerning_value=0.0):
            if not text:
                # If text is empty, return a black canvas directly
                canvas_width, canvas_height = 40, 40  # Set desired dimensions for an empty canvas
                bg_color = ImageColor.getrgb(background_color_hex)
                canvas = Image.new("RGB", (canvas_width, canvas_height), bg_color)
                image_tensor_out = torch.tensor(np.array(canvas) / 255.0, dtype=torch.float32).unsqueeze(0)
                return image_tensor_out,

            bg_color = ImageColor.getrgb(background_color_hex)
            font_color = ImageColor.getrgb(font_color_hex)

            # Initial font size and maximum attempts for fitting text
            current_font_size = font_size
            max_attempts = 10

            for _ in range(max_attempts):
                font = ImageFont.truetype(font_path, current_font_size)

                # Calculate actual text width with kerning
                actual_text_width = sum(font.getsize(ch)[0] + kerning_value for ch in text)

                # Calculate text height
                text_height = font.getsize(text)[1]

                # Create canvas with appropriate width and height (using integers)
                canvas_width = int(actual_text_width + 40)
                canvas_height = int(text_height + 40)
                canvas = Image.new("RGB", (canvas_width, canvas_height), bg_color)

                # Draw text with adjusted font size and kerning (using integers for coordinates)
                draw = ImageDraw.Draw(canvas)
                x = (canvas_width - actual_text_width) // 2
                y = (canvas_height - text_height) // 2

                for ch in text:
                    ch_width, _ = font.getsize(ch)
                    draw.text((x, y), ch, fill=font_color, font=font)
                    x += ch_width + int(kerning_value)  # Add integers for positioning

                # Convert to PyTorch tensor efficiently
                image_tensor_out = torch.tensor(np.array(canvas) / 255.0, dtype=torch.float32).unsqueeze(0)

                return image_tensor_out,

NODE_CLASS_MAPPINGS = {
    "🏷️ FATLABEL (Basic)": BasicFatLabel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasicFatLabel": "🏷️ FATLABEL (Basic)",

}