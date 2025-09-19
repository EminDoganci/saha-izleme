# device.py

import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import time
import sys
from .forms import EditDeviceForm
from .config import *
from PIL import Image, ImageTk

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

        self.circle_size = 20
        
        self.label_font = ("Arial", 10, "bold")

        self.circle = self.canvas.create_oval(0, 0, 0, 0, fill="red", outline="yellow", width=1.5)
        
        self.pulsing_circles = [
            self.canvas.create_oval(0, 0, 0, 0, fill="", outline=""),
            self.canvas.create_oval(0, 0, 0, 0, fill="", outline=""),
            self.canvas.create_oval(0, 0, 0, 0, fill="", outline="")
        ]
        
        self.label = self.canvas.create_text(0, 0, text=name, anchor="w", font=self.label_font, fill="#2c3e50")
        
        self.update_position_from_original()

        # Görsel hiyerarşiyi düzenledik
        self.canvas.tag_raise(self.circle)
        for p_circle in self.pulsing_circles:
            self.canvas.tag_lower(p_circle, self.circle)
        self.canvas.tag_raise(self.label) 
        
        self.canvas.tag_bind(self.circle, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.label, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.circle, "<Button-1>", self.start_drag)
        self.canvas.tag_bind(self.label, "<Button-1>", self.start_drag) 
        self.canvas.tag_bind(self.circle, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)
        
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
        
        self.canvas.coords(
            self.circle,
            canvas_x - scaled_circle_size,
            canvas_y - scaled_circle_size,
            canvas_x + scaled_circle_size,
            canvas_y + scaled_circle_size
        )
        self.canvas.coords(self.label, canvas_x + scaled_circle_size + 5, canvas_y)
        
        for p_circle in self.pulsing_circles:
            self.canvas.coords(
                p_circle,
                canvas_x - scaled_circle_size,
                canvas_y - scaled_circle_size,
                canvas_x + scaled_circle_size,
                canvas_y + scaled_circle_size
            )

    def start_drag(self, event):
        if not self.is_locked:
            self.drag_data = {"item": self.circle, "x": event.x, "y": event.y}
            self.canvas.tag_raise(self.circle)
            for p_circle in self.pulsing_circles:
                self.canvas.tag_lower(p_circle, self.circle)
            self.canvas.tag_raise(self.label) 

    def on_drag(self, event):
        if not self.is_locked and self.drag_data:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            self.canvas.move(self.circle, dx, dy)
            self.canvas.move(self.label, dx, dy)
            for p_circle in self.pulsing_circles:
                self.canvas.move(p_circle, dx, dy)
            
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
        # Önemli Düzeltme: `root` ve `self` (cihaz nesnesi) parametrelerini gönderiyoruz.
        EditDeviceForm(self.app.root, self)

    def delete_device(self):
        if messagebox.askyesno("Cihazı Sil", f"{self.name} cihazını silmek istediğinizden emin misiniz?"):
            self.is_alive = False
            
            if self.animation_id:
                try:
                    self.canvas.after_cancel(self.animation_id)
                except ValueError:
                    pass

            self.canvas.delete(self.circle)
            self.canvas.delete(self.label)
            for p_circle in self.pulsing_circles:
                self.canvas.delete(p_circle)
            
            # Bu satırın varlığına dikkat edin, önemli!
            if self in self.app.devices:
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
        
        coords = self.canvas.coords(self.circle)
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        
        self.canvas.itemconfigure(self.circle, fill="#00ff00", outline="#00ff00")
        
        current_time = time.time()
        base_speed = 1.0
        
        for i, circle in enumerate(self.pulsing_circles):
            delay = i * 0.2 
            pulse_value = (current_time * base_speed + delay) % 1
            
            size = self.circle_size * self.app.current_scale * (1 + pulse_value * 6) 
            
            alpha_value = int(255 * (1 - pulse_value) * 0.8)
            hex_color = f'#00{alpha_value:02x}00'

            x0 = center_x - size / 2
            y0 = center_y - size / 2
            x1 = center_x + size / 2
            y1 = center_y + size / 2

            self.canvas.coords(circle, x0, y0, x1, y1)
            self.canvas.itemconfigure(circle, outline=hex_color, fill="", width=1)

        self.animation_id = self.canvas.after(20, self.breathing_animation)

    def flashing_animation(self):
        if not self.is_alive or self.is_reachable: return

        coords = self.canvas.coords(self.circle)
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        
        self.canvas.itemconfigure(self.circle, fill="#ff0000", outline="#ff0000")

        current_time = time.time()
        base_speed = 2.0
        
        for i, circle in enumerate(self.pulsing_circles):
            delay = i * 0.2 
            pulse_value = (current_time * base_speed + delay) % 1
            
            size = self.circle_size * self.app.current_scale * (1 + pulse_value * 40) 
            
            alpha_value = int(255 * (1 - pulse_value) * 0.8)
            hex_color = f'#{alpha_value:02x}0000'

            x0 = center_x - size / 2
            y0 = center_y - size / 2
            x1 = center_x + size / 2
            y1 = center_y + size / 2

            self.canvas.coords(circle, x0, y0, x1, y1)
            self.canvas.itemconfigure(circle, outline=hex_color, fill="", width=1)

        self.animation_id = self.canvas.after(20, self.flashing_animation)
