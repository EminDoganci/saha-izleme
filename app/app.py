# app.py

import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ExifTags
import sys
from .device import Device
from .ui_panels import DeviceListPanel
from .forms import DeviceForm
from .config import *

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Saha İzleme")
        self.root.geometry("1200x800")
        self.root.bind("<Configure>", self.on_resize)
        self.image = None
        self.original_image = None
        self.photo = None
        self.image_id = None
        self.devices = []
        self.current_scale = 1.0
        self.pending_device_data = {}

        self.button_frame = tk.Frame(root, bg=BG_COLOR_DARK)
        self.button_frame.pack(side="top", fill="x")

        tk.Button(self.button_frame, text="Harita Yükle", command=self.load_map, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)
        tk.Button(self.button_frame, text="Cihaz Ekle", command=self.show_add_form, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)
        
        self.main_frame = tk.Frame(root, bg=BG_COLOR_DARK)
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg=BG_COLOR_DARK, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan_map)
        self.canvas.bind("<MouseWheel>", self.zoom)

        self.pan_start = None
        self.device_list_panel = DeviceListPanel(self.main_frame, self)
        self.load_map(initial_load=True)

    def on_resize(self, event):
        if self.original_image:
            self.load_map_to_fit()

    def load_map(self, initial_load=False):
        file_path = "dom_screennail+.png" if initial_load else filedialog.askopenfilename()
        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            
            try:
                exif = self.original_image._getexif()
                if exif:
                    for tag, value in exif.items():
                        if ExifTags.TAGS.get(tag) == 'Orientation':
                            if value == 3:
                                self.original_image = self.original_image.rotate(180, expand=True)
                            elif value == 6:
                                self.original_image = self.original_image.rotate(270, expand=True)
                            elif value == 8:
                                self.original_image = self.original_image.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                self.original_image = self.original_image.rotate(270, expand=True)

            self.load_map_to_fit()

        except Exception as e:
            messagebox.showerror("Hata", f"Harita yüklenemedi: {e}")

    def load_map_to_fit(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width == 1 and canvas_height == 1:
            self.root.after(100, self.load_map_to_fit)
            return
            
        img_width, img_height = self.original_image.size
        
        ratio = min(canvas_width / img_width, canvas_height / img_height)
        self.current_scale = ratio
        new_width = int(img_width * self.current_scale)
        new_height = int(img_height * self.current_scale)

        self.image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)
        
        if self.image_id:
            self.canvas.delete(self.image_id)
        
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        self.image_id = self.canvas.create_image(center_x, center_y, image=self.photo, anchor="center")
        self.canvas.tag_lower(self.image_id)

        for device in self.devices:
            device.update_position_from_original()

    def start_pan(self, event):
        self.pan_start = (event.x, event.y)
        
    def pan_map(self, event):
        if self.pan_start:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            
            self.canvas.move("all", dx, dy)
            self.pan_start = (event.x, event.y)

    def zoom(self, event):
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        if sys.platform.startswith("linux"):
            zoom_factor = 1.1 if event.delta < 0 else 0.9

        old_scale = self.current_scale
        self.current_scale *= zoom_factor

        new_width = int(self.original_image.width * self.current_scale)
        new_height = int(self.original_image.height * self.current_scale)
        self.image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

        old_center_x, old_center_y = self.canvas.coords(self.image_id)
        new_center_x = event.x - (event.x - old_center_x) * (self.current_scale / old_scale)
        new_center_y = event.y - (event.y - old_center_y) * (self.current_scale / old_scale)
        
        self.canvas.coords(self.image_id, new_center_x, new_center_y)
        self.canvas.itemconfig(self.image_id, image=self.photo)

        for device in self.devices:
            device.update_position_from_original()

    def show_add_form(self):
        if not self.image_id:
            messagebox.showinfo("Bilgi", "Lütfen önce bir harita yükleyin.")
            return

        DeviceForm(self.root, self.on_form_submit)

    def on_form_submit(self, name, ip, device_type, model, connected_port, starting_port):
        self.pending_device_data = {
            "name": name,
            "ip": ip,
            "device_type": device_type,
            "model": model,
            "connected_port": connected_port,
            "starting_port": starting_port
        }
        self.canvas.config(cursor="cross")
        messagebox.showinfo("Bilgi", "Lütfen cihazı eklemek istediğiniz yere tıklayın.")
        self.canvas.bind("<Button-1>", self.add_device_on_canvas)

    def add_device_on_canvas(self, event):
        self.canvas.config(cursor="")
        self.canvas.unbind("<Button-1>")

        map_coords = self.canvas.coords(self.image_id)
        if not map_coords: return

        map_x_center = map_coords[0]
        map_y_center = map_coords[1]
        
        original_x = (event.x - map_x_center + (self.image.width / 2)) / self.current_scale
        original_y = (event.y - map_y_center + (self.image.height / 2)) / self.current_scale
        
        data = self.pending_device_data
        
        new_device = Device(self.canvas, self, data["name"], data["ip"], original_x, original_y, data["device_type"], data["model"], data["connected_port"], data["starting_port"])
        self.devices.append(new_device)
        self.device_list_panel.update_device_list()