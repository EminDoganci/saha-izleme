# ui_panels.py

import tkinter as tk
import time
from .config import *

class DeviceListPanel:
    def __init__(self, master, app):
        self.app = app
        # Arka plan rengi değiştirildi
        self.frame = tk.Frame(master, bg=BG_COLOR_DARK)
        self.frame.pack(side="right", fill="y", padx=10, pady=10)
        # Yazı rengi değiştirildi
        self.label = tk.Label(self.frame, text="Bağlı Cihazlar", font=FONT_HEADING, bg=BG_COLOR_DARK, fg=FG_COLOR)
        self.label.pack(pady=10)
        
        # Arka plan rengi değiştirildi
        self.list_frame = tk.Frame(self.frame, bg=BG_COLOR_LIST)
        self.list_frame.pack(fill="both", expand=True)

        self.device_items = {}
        self.animation_ids = {}

    def update_device_list(self):
        for anim_id in self.animation_ids.values():
            try:
                self.app.root.after_cancel(anim_id)
            except (ValueError, KeyError):
                pass
        self.animation_ids = {}
        
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        self.device_items = {}
        
        for device in self.app.devices:
            item_frame = tk.Frame(self.list_frame, bg=BG_COLOR_MEDIUM)
            item_frame.pack(fill="x", pady=2, padx=5)
            
            status_canvas = tk.Canvas(item_frame, width=15, height=15, bg=BG_COLOR_MEDIUM, highlightthickness=0)
            status_canvas.pack(side="left", padx=5)
            circle = status_canvas.create_oval(3, 3, 12, 12, outline="", fill="")
            
            device_label = tk.Label(item_frame, text=device.name, bg=BG_COLOR_MEDIUM, fg=FG_COLOR, font=FONT_DEFAULT)
            device_label.pack(side="left", padx=5)
            
            self.device_items[device.name] = {
                "frame": item_frame,
                "canvas": status_canvas,
                "circle": circle,
                "device_ref": device
            }
            
            self.animate_list_item(device)

    def animate_list_item(self, device):
        if not device.is_alive or device.name not in self.device_items:
            if device.name in self.animation_ids:
                try:
                    self.app.root.after_cancel(self.animation_ids[device.name])
                except (ValueError, KeyError):
                    pass
                del self.animation_ids[device.name]
            return
            
        item = self.device_items[device.name]
        
        if device.is_reachable:
            pulse_value = abs(time.time() * 2 % 2 - 1)
            green_val = int(255 * (0.5 + 0.5 * pulse_value))
            fill_color_hex = f'#00{green_val:02x}00'
            outline_color = "green"
            item["canvas"].itemconfig(item["circle"], fill=fill_color_hex)
            item["canvas"].itemconfig(item["circle"], outline=outline_color)
        else:
            pulse_value = abs(time.time() * 2 % 2 - 1)
            if pulse_value > 0.5:
                fill_color_hex = "red"
                outline_color = "red"
            else:
                fill_color_hex = BG_COLOR_MEDIUM
                outline_color = "red"
            
            item["canvas"].itemconfig(item["circle"], fill=fill_color_hex)
            item["canvas"].itemconfig(item["circle"], outline=outline_color)

        anim_id = self.app.root.after(ANIMATION_DELAY_MS, lambda: self.animate_list_item(device))
        self.animation_ids[device.name] = anim_id
