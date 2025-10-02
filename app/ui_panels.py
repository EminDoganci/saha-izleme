import tkinter as tk
import time
import sys
from .config import *

class DeviceListPanel:
    def __init__(self, master, app):
        self.app = app
        self.frame = tk.Frame(master, bg=BG_COLOR_DARK)
        self.frame.pack(side="right", fill="y", padx=10, pady=10)
        
        self.label = tk.Label(self.frame, text="Bağlı Cihazlar", font=FONT_HEADING, bg=BG_COLOR_DARK, fg=FG_COLOR)
        self.label.pack(pady=5)
        
        self.canvas = tk.Canvas(self.frame, bg=BG_COLOR_LIST, highlightthickness=0, width=180)
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_COLOR_LIST)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=False)
        self.scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            if sys.platform.startswith("win"):
                self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
            else:
                self.canvas.yview_scroll(-1 * int(event.delta), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self.device_items = {}
        self.animation_ids = {}
        self.animation_id_global = None  

        # Global animasyon başlat
        self.animate_all_items()

    def update_device_list(self):
        for anim_id in list(self.animation_ids.values()):
            try:
                self.app.root.after_cancel(anim_id)
            except (ValueError, KeyError):
                pass
        self.animation_ids.clear()
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.device_items.clear()
        
        for device in self.app.devices:
            self.add_device_to_list(device)

        # Global animasyonu yeniden başlat
        if self.animation_id_global:
            self.app.root.after_cancel(self.animation_id_global)
        self.animate_all_items()

    def clear_listbox(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for anim_id in list(self.animation_ids.values()):
            try:
                self.app.root.after_cancel(anim_id)
            except (ValueError, KeyError):
                pass
        self.animation_ids.clear()
        self.device_items.clear()

        if self.animation_id_global:
            self.app.root.after_cancel(self.animation_id_global)
        self.animation_id_global = None

    def add_device_to_list(self, device):
        item_frame = tk.Frame(self.scrollable_frame, bg=BG_COLOR_MEDIUM)
        item_frame.pack(fill="x", pady=2, padx=2)
        
        item_frame.bind("<Button-1>", lambda event, dev=device: self.app.set_selected_device(dev))
        
        status_canvas = tk.Canvas(item_frame, width=12, height=12, bg=BG_COLOR_MEDIUM, highlightthickness=0)
        status_canvas.pack(side="left", padx=2)
        status_canvas.bind("<Button-1>", lambda event, dev=device: self.app.set_selected_device(dev))
        
        circle = status_canvas.create_oval(3, 3, 9, 9, outline="", fill="")
        
        device_label = tk.Label(item_frame, text=device.name, bg=BG_COLOR_MEDIUM, fg=FG_COLOR, font=("Arial", 8))
        device_label.pack(side="left", padx=2)
        device_label.bind("<Button-1>", lambda event, dev=device: self.app.set_selected_device(dev))
        
        self.device_items[device] = {
            "frame": item_frame,
            "canvas": status_canvas,
            "circle": circle,
        }
        
        fill_color = "#00ff00" if device.is_reachable else "red"
        status_canvas.itemconfig(circle, fill=fill_color)

    def animate_all_items(self):
        if not self.app.devices:
            return

        pulse_value = abs(time.time() * 2 % 2 - 1)

        for device in self.app.devices:
            if not device.is_alive or device not in self.device_items:
                continue

            item = self.device_items[device]

            if device.is_reachable:
                green_val = int(255 * (0.5 + 0.5 * pulse_value))
                fill_color_hex = f'#00{green_val:02x}00'
                item["canvas"].itemconfig(item["circle"], fill=fill_color_hex, outline="green")
            else:
                if pulse_value > 0.5:
                    fill_color_hex = "red"
                else:
                    fill_color_hex = BG_COLOR_MEDIUM
                item["canvas"].itemconfig(item["circle"], fill=fill_color_hex, outline="red")

        self.animation_id_global = self.app.root.after(ANIMATION_DELAY_MS, self.animate_all_items)
