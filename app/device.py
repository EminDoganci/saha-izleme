import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import time
import sys
import os
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
        self.ping_thread = None
        self.process = None

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

        self.canvas.tag_raise(self.circle)
        for p_circle in self.pulsing_circles:
            self.canvas.tag_lower(p_circle, self.circle)
        self.canvas.tag_raise(self.label)

        self.canvas.tag_bind(self.circle, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.label, "<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.circle, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.label, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.circle, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)

        self.ping_interval = self.app.ping_interval
        
        self.start_ping_thread()

    def on_click(self, event):
        self.app.set_selected_device(self)
        self.start_drag(event)

    def start_ping_thread(self):
        if self.ping_thread and self.ping_thread.is_alive():
            self.is_alive = False
            self.ping_thread.join(timeout=1)
            if self.ping_thread.is_alive():
                print(f"{self.name} için eski ping thread'i sonlandırılamadı.")

        self.is_alive = True
        self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
        self.ping_thread.start()

    def ping_loop(self):
        while self.is_alive:
            try:
                new_status = self._perform_ping()
                if new_status != self.is_reachable:
                    self.app.root.after(0, self.update_visual_and_list, new_status)
                else:
                   
                    self.app.root.after(0, self.update_visual, new_status)
            except Exception as e:
                print(f"Ping döngüsü hatası: {e}")
                self.app.root.after(0, self.update_visual_and_list, False)
                break
            time.sleep(self.ping_interval)

    def _perform_ping(self):
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
                timeout=3,
                creationflags=creation_flags
            )
            
            if sys.platform.startswith("win"):
                
                stdout_lower = result.stdout.lower()
                if "destination host unreachable" in stdout_lower:
                    return False
                if "request timed out" in stdout_lower:
                    return False
                if "received = 1" in result.stdout or "alındı = 1" in result.stdout or "ttl=" in stdout_lower:
                    return True
                return False
            else:
                return result.returncode == 0
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
        except Exception as e:
            print(f"Ping işlemi sırasında beklenmedik hata: {e}")
            return False

    def set_ping_interval(self, interval):
        if self.ping_interval != interval:
            self.ping_interval = interval
            self.start_ping_thread()

    def edit_device_info(self, name, ip, device_type, model, connected_port, starting_port):
        old_ip = self.ip
        self.name = name
        self.ip = ip
        self.device_type = device_type
        self.model = model
        self.connected_port = connected_port
        self.starting_port = starting_port
        
        self.canvas.itemconfigure(self.label, text=self.name)
        
        if old_ip != self.ip:
            self.start_ping_thread()
            
            
            def immediate_ping_check():
                try:
                    new_status = self._perform_ping()
                    self.app.root.after(0, self.update_visual_and_list, new_status)
                except Exception as e:
                    print(f"Anlık ping hatası: {e}")
                    self.app.root.after(0, self.update_visual_and_list, False)
            
            threading.Thread(target=immediate_ping_check, daemon=True).start()

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
        self.app.set_selected_device(self)
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(label="Düzenle", command=self.edit_device)
        menu.add_command(label="Sil", command=self.delete_device)
        menu.add_separator()
        menu.add_command(label="Ping At", command=self.ping_with_terminal)

        if self.is_locked:
            menu.add_command(label="Kilidi Aç", command=self.toggle_lock)
        else:
            menu.add_command(label="Kilitle", command=self.toggle_lock)
            
        menu.post(event.x_root, event.y_root)
        
        return "break"

    def edit_device(self):
        EditDeviceForm(self.app.root, self)

    def delete_device(self):
        if messagebox.askyesno("Cihazı Sil", f"{self.name} cihazını silmek istediğinizden emin misiniz?"):
            self.is_alive = False
            if self.ping_thread and self.ping_thread.is_alive():
                self.ping_thread.join(timeout=1)

            if self.animation_id:
                try:
                    self.canvas.after_cancel(self.animation_id)
                except ValueError:
                    pass

            self.canvas.delete(self.circle)
            self.canvas.delete(self.label)
            for p_circle in self.pulsing_circles:
                self.canvas.delete(p_circle)
            
            
            if hasattr(self.app, 'ping_worker') and self in self.app.ping_worker.devices_to_check:
                self.app.ping_worker.devices_to_check.remove(self)

            if self in self.app.devices:
                self.app.devices.remove(self)
            
            self.app.device_list_panel.update_device_list()
            self.app.set_selected_device(None) 
            
    
    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.update_visual(self.is_reachable)  
        self.app.device_list_panel.update_device_list()
            
    def ping_with_terminal(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Bilgi", "Bu cihaz için zaten bir ping işlemi çalışıyor.")
            return

        try:
            if sys.platform.startswith("win"):
                cmd = f"ping {self.ip} -t"
                messagebox.showinfo("Bilgi", f"{self.name} cihazına ({self.ip}) ping atılıyor.\n\nCMD penceresinde görülen IP, ağ yönlendirmesi veya yerel makine IP’si olabilir.\n\nUygulama içindeki durum, gerçek ping sonucunu yansıtır.")
                self.process = subprocess.Popen(
                    ["start", "cmd", "/k", cmd],
                    shell=True
                )
            else:
                terminal_command = ["xterm", "-e", f"ping {self.ip}"]
                self.process = subprocess.Popen(
                    terminal_command,
                    shell=False
                )
        except FileNotFoundError:
            messagebox.showerror("Hata", "Terminal bulunamadı. Lütfen bir terminal emülatörü (xterm, gnome-terminal) kurun.")
        except Exception as e:
            messagebox.showerror("Hata", f"Ping başlatılamadı: {e}")
            
    def update_visual_and_list(self, new_status):
        self.is_reachable = new_status
        self.update_visual(new_status)
        self.app.device_list_panel.update_device_list()
            
    def update_visual(self, new_status):
        if self.is_reachable:
            self.canvas.itemconfigure(self.circle, fill="#00ff00", outline="#00ff00" if not self.is_locked else "green")
        else:
            self.canvas.itemconfigure(self.circle, fill="#ff0000", outline="#ff0000" if not self.is_locked else "red")
            
        if self.is_locked:
            self.canvas.itemconfigure(self.circle, width=2)
        else:
            self.canvas.itemconfigure(self.circle, width=1.5)

        if self.animation_id:
            try:
                self.canvas.after_cancel(self.animation_id)
            except ValueError:
                pass
        self.start_animation()
            
    def start_animation(self):
        if not self.is_alive:
            return
            
        if self.is_reachable:
            self.breathing_animation()
        else:
            self.flashing_animation()

    def breathing_animation(self):
        if not self.is_alive or not self.is_reachable: return
        
        coords = self.canvas.coords(self.circle)
        if not coords: return
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        
        self.canvas.itemconfigure(self.circle, fill="#00ff00", outline="#00ff00" if not self.is_locked else "green")
        
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
        if not coords: return
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        
        self.canvas.itemconfigure(self.circle, fill="#ff0000", outline="#ff0000" if not self.is_locked else "red")

        current_time = time.time()
        base_speed = 2.0
        
        for i, circle in enumerate(self.pulsing_circles):
            delay = i * 0.2  
            pulse_value = (current_time * base_speed + delay) % 1
            
            size = self.circle_size * self.app.current_scale * (1 + pulse_value * 40)  
            
            alpha_value = int(255 * (1 - pulse_value) * 0.8)
            
            hex_color = f'#{max(alpha_value, 60):02x}0000'

            x0 = center_x - size / 2
            y0 = center_y - size / 2
            x1 = center_x + size / 2
            y1 = center_y + size / 2

            self.canvas.coords(circle, x0, y0, x1, y1)
            
            self.canvas.itemconfigure(circle, outline=hex_color, fill="", width=2)

        self.animation_id = self.canvas.after(20, self.flashing_animation)
