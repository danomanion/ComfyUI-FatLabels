"""
@forker: LaminarRainbow 
@title: FAT LABELS
@nickname: FAT LABELS
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
fat_labels__path = os.path.join(os.path.dirname(__file__))

def handle_stream(stream, is_stdout):
    stream.reconfigure(encoding=locale.getpreferredencoding(), errors='replace')

    for msg in stream:
        if is_stdout:
            print(msg, end="", file=sys.stdout)
        else: 
            print(msg, end="", file=sys.stderr)


def process_wrap(cmd_str, cwd=None, handler=None):
    print(f"[Fat Labels] EXECUTE: {cmd_str} in '{cwd}'")
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

print("### FAT LABELS: Check dependencies")

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

print(f"### Loading: Fat Labels (V0.2.1)")

class FatLabels:
    def __init__(self, device="cpu"):
        self.device = device

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "Hello"}),
                "font_path": ("STRING", {"default": f"{fat_labels__path}/fonts/Bevan-Regular.ttf", "multiline": False}),
                "font_color_hex": ("STRING", {"default": "#FFFFFF", "multiline": False}),
                "background_color_hex": ("STRING", {"default": "#000000", "multiline": False}),
                "font_size": ("INT", {"default": 72, "min": 1}),  # Font size in pixels
                "kerning_value": ("FLOAT", {"default": 0.0}),  # New input for kerning
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "create_fat_label"
    CATEGORY = "image/text"

    def create_fat_label(self, text, background_color_hex, font_color_hex, font_path, font_size, kerning_value):
        bg_color = ImageColor.getrgb(background_color_hex)
        font_color = ImageColor.getrgb(font_color_hex)

        # Calculate text dimensions directly without creating a temporary canvas
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = font.getsize(text)

        # Create canvas with appropriate dimensions and padding
        canvas_width = text_width + 40  # Add 20px padding on each side
        canvas_height = text_height + 40
        canvas = Image.new("RGB", (canvas_width, canvas_height), bg_color)

        # Draw text directly on the canvas
        draw = ImageDraw.Draw(canvas)
        x = (canvas_width - text_width) // 2
        y = (canvas_height - text_height) // 2

        for i in range(len(text) - 1):
            ch = text[i]
            ch_width, ch_height = font.getsize(ch)
            draw.text((x, y), ch, fill=font_color, font=font)
            x += ch_width + kerning_value  # Add kerning value between characters
        draw.text((x, y), text[-1], fill=font_color, font=font)  # Draw the last character

        # Convert to PyTorch tensor efficiently
        image_tensor_out = torch.tensor(np.array(canvas) / 255.0, dtype=torch.float32).unsqueeze(0)

        return (image_tensor_out,)


NODE_CLASS_MAPPINGS = {
    "FatLabels": FatLabels,
}
