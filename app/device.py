# device.py

import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import time
import sys
from .forms import EditDeviceForm
from .config import *

class Device:
    def __init__(self, canvas, app, name, ip, x, y, device_type, model, connected_port, starting_port):
        self.canvas = canvas
        self.app = app
        self.name = name
        self.ip = ip
        self.device_type = device_type
        self.model = model
        self.connected_port = connected_port
        self.starting_port = starting_port
        self.is_reachable = False
        self.is_locked = False
        self.animation_id = None
        self.drag_data = None
        self.is_alive = True
        
        self.original_x = x
        self.original_y = y

        self.circle_size = 20  # Yuvarlak boyutu 20 olarak ayarlandı
        
        self.label_font = ("Arial", 10, "bold")

        # Önce arka planı oluştur (rectangle)
        self.label_bg = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", stipple="gray25", outline="")
        self.circle = self.canvas.create_oval(0, 0, 0, 0, fill="red", outline="yellow", width=1.5)
        self.pulsing_circle = self.canvas.create_oval(0, 0, 0, 0, fill="", outline="")
        self.label = self.canvas.create_text(0, 0, text=name, anchor="w", font=self.label_font, fill="white")
        
        self.update_position_from_original()

        self.canvas.tag_raise(self.label_bg)
        self.canvas.tag_raise(self.circle)
        self.canvas.tag_raise(self.pulsing_circle)
        self.canvas.tag_raise(self.label)
        
        # Etkileşim için bağlamalar
        self.canvas.tag_bind(self.circle, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.label, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.circle, "<Button-1>", self.start_drag)
        self.canvas.tag_bind(self.label, "<Button-1>", self.start_drag) 
        self.canvas.tag_bind(self.circle, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)
        
        # Fareyle üzerine gelme (hover) olayları kaldırıldı

        self.ping_thread = threading.Thread(target=self.ping_host, daemon=True)
        self.ping_thread.start()

    def update_position_from_original(self):
        x_on_map = self.original_x * self.app.current_scale
        y_on_map = self.original_y * self.app.current_scale
        
        map_coords = self.canvas.coords(self.app.image_id)
        if not map_coords: return
        map_x_center = map_coords[0]
        map_y_center = map_coords[1]

        canvas_x = map_x_center + x_on_map - (self.app.image.width / 2)
        canvas_y = map_y_center + y_on_map - (self.app.image.height / 2)

        scaled_circle_size = self.circle_size * self.app.current_scale
        
        # Etiketin genişliğini dinamik olarak ayarla
        bbox = self.canvas.bbox(self.label)
        if not bbox:
            text_width = 0
        else:
            text_width = bbox[2] - bbox[0]
            
        label_x1 = canvas_x + scaled_circle_size + 3
        label_y1 = canvas_y - 10
        label_x2 = label_x1 + text_width + 10
        label_y2 = canvas_y + 10

        self.canvas.coords(
            self.circle,
            canvas_x - scaled_circle_size,
            canvas_y - scaled_circle_size,
            canvas_x + scaled_circle_size,
            canvas_y + scaled_circle_size
        )
        self.canvas.coords(self.label_bg, label_x1, label_y1, label_x2, label_y2)
        self.canvas.coords(self.label, label_x1 + 5, canvas_y)
        self.canvas.coords(
            self.pulsing_circle,
            canvas_x - scaled_circle_size,
            canvas_y - scaled_circle_size,
            canvas_x + scaled_circle_size,
            canvas_y + scaled_circle_size
        )
        self.canvas.tag_raise(self.label_bg)
        self.canvas.tag_raise(self.circle)
        self.canvas.tag_raise(self.label)
        self.canvas.tag_raise(self.pulsing_circle)

    def start_drag(self, event):
        if not self.is_locked:
            self.drag_data = {"item": self.circle, "x": event.x, "y": event.y}
            self.canvas.tag_raise(self.label_bg)
            self.canvas.tag_raise(self.circle)
            self.canvas.tag_raise(self.label)
            self.canvas.tag_raise(self.pulsing_circle)

    def on_drag(self, event):
        if not self.is_locked and self.drag_data:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            self.canvas.move(self.circle, dx, dy)
            self.canvas.move(self.label_bg, dx, dy)
            self.canvas.move(self.label, dx, dy)
            self.canvas.move(self.pulsing_circle, dx, dy)
            
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

            map_coords = self.canvas.coords(self.app.image_id)
            map_x_center = map_coords[0]
            map_y_center = map_coords[1]
            
            coords = self.canvas.coords(self.circle)
            x_center = (coords[0] + coords[2]) / 2
            y_center = (coords[1] + coords[3]) / 2

            self.original_x = (x_center - map_x_center + (self.app.image.width / 2)) / self.app.current_scale
            self.original_y = (y_center - map_y_center + (self.app.image.height / 2)) / self.app.current_scale
    
    def show_context_menu(self, event):
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(label="Düzenle", command=self.edit_device)
        menu.add_command(label="Sil", command=self.delete_device)
        
        if self.is_locked:
            menu.add_command(label="Kilidi Aç", command=self.toggle_lock)
        else:
            menu.add_command(label="Kilitle", command=self.toggle_lock)
            
        menu.post(event.x_root, event.y_root)
        
        return "break"

    def edit_device(self):
        EditDeviceForm(self.canvas, self)

    def delete_device(self):
        if messagebox.askyesno("Cihazı Sil", f"{self.name} cihazını silmek istediğinizden emin misiniz?"):
            self.is_alive = False
            
            if self.animation_id:
                try:
                    self.canvas.after_cancel(self.animation_id)
                except ValueError:
                    pass

            self.canvas.delete(self.circle)
            self.canvas.delete(self.label_bg)
            self.canvas.delete(self.label)
            self.canvas.delete(self.pulsing_circle)
            
            self.app.devices.remove(self)
            self.app.device_list_panel.update_device_list()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.canvas.itemconfigure(self.circle, outline="green" if self.is_reachable else "red", width=2)
        else:
            self.canvas.itemconfigure(self.circle, outline="yellow", width=1)
            
    def ping_host(self):
        is_first_ping = True
        while self.is_alive:
            try:
                if sys.platform.startswith("win"):
                    param = "-n"
                    creation_flags = subprocess.CREATE_NO_WINDOW
                else:
                    param = "-c"
                    creation_flags = 0
                
                command = ["ping", param, "1", self.ip]
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    creationflags=creation_flags
                )
                
                new_status = result.returncode == 0
                
                if new_status != self.is_reachable or is_first_ping:
                    self.is_reachable = new_status
                    self.canvas.after(0, self.start_animation)
                    self.app.device_list_panel.update_device_list()
            
            except (subprocess.TimeoutExpired, FileNotFoundError):
                new_status = False
                if new_status != self.is_reachable or is_first_ping:
                    self.is_reachable = new_status
                    self.canvas.after(0, self.start_animation)
                    self.app.device_list_panel.update_device_list()
            except Exception as e:
                print(f"Ping hatası: {e}")
                
            is_first_ping = False
            time.sleep(PING_INTERVAL_SECONDS)

    def start_animation(self):
        if not self.is_alive:
            return
            
        if self.animation_id:
            try:
                self.canvas.after_cancel(self.animation_id)
            except ValueError:
                pass

        if self.is_reachable:
            self.breathing_animation()
        else:
            self.flashing_animation()

    def breathing_animation(self):
        if not self.is_alive or not self.is_reachable: return
        
        pulse_value = abs(time.time() * 2 % 2 - 1)
        green_val = int(255 * (0.5 + 0.5 * pulse_value))
        hex_color = '#%02x%02x%02x' % (0, green_val, 0)
        
        self.canvas.itemconfigure(self.circle, fill=hex_color)
        self.canvas.itemconfigure(self.pulsing_circle, outline="")
        
        if not self.is_locked:
            self.canvas.itemconfigure(self.circle, outline="green")
        
        self.animation_id = self.canvas.after(50, self.breathing_animation)

    def flashing_animation(self):
        if not self.is_alive or self.is_reachable: return
        
        pulse_value = abs(time.time() * 2 % 2 - 1)
        pulse_scale = 1 + pulse_value * 2 
        
        coords = self.canvas.coords(self.circle)
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        
        size = self.circle_size * self.app.current_scale * pulse_scale
        
        hex_color = '#%02x%02x%02x' % (255, 0, 0)
        
        self.canvas.coords(
            self.pulsing_circle,
            center_x - size,
            center_y - size,
            center_x + size,
            center_y + size
        )
        self.canvas.itemconfigure(self.pulsing_circle, outline=hex_color, width=3)

        self.canvas.itemconfigure(self.circle, fill="red", outline="red")
        
        if not self.is_locked:
            self.canvas.itemconfigure(self.circle, outline="red")
            
        self.animation_id = self.canvas.after(50, self.flashing_animation)