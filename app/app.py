import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk, ExifTags
import sys
import json
import threading
import time  # 👈 EKLENDİ — PingWorker için gerekli
from .device import Device
from .ui_panels import DeviceListPanel
from .forms import AddDeviceForm, EditDeviceForm
from .config import *
import os

class PingWorker:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None
        self.devices_to_check = []

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _worker_loop(self):
        while self.running:
            try:
                devices = self.devices_to_check.copy()
                self.devices_to_check.clear()

                for device in devices:
                    if not device.is_alive:
                        continue
                    try:
                        status = device._perform_ping()
                        if status != device.is_reachable:
                            self.app.root.after(0, device.update_visual_and_list, status)
                        else:
                            self.app.root.after(0, device.update_visual, status)
                    except Exception as e:
                        print(f"Ping hatası: {e}")
                        self.app.root.after(0, device.update_visual_and_list, False)
            except Exception as e:
                print(f"Worker hatası: {e}")

            time.sleep(1)  # Her 1 saniyede bir kontrol

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
        self.map_file_path = None
        self.ping_interval = PING_INTERVAL_SECONDS
        self.selected_device = None

        # PingWorker başlat
        self.ping_worker = PingWorker(self)
        self.ping_worker.start()

        self.button_frame = tk.Frame(root, bg=BG_COLOR_DARK)
        self.button_frame.pack(side="top", fill="x")

        tk.Button(self.button_frame, text="Harita Yükle", command=self.load_map, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)
        tk.Button(self.button_frame, text="Cihaz Ekle", command=self.show_add_form, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)
        
        self.ping_button = tk.Button(self.button_frame, text="Seçili Cihaza Ping At", command=self.ping_selected_device, state="disabled", bg=BG_COLOR_MEDIUM, fg=FG_COLOR)
        self.ping_button.pack(side="left", padx=5, pady=5)
        
        tk.Button(self.button_frame, text="Projeyi Kaydet", command=self.save_project, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)
        tk.Button(self.button_frame, text="Projeyi Aç", command=self.load_project, bg=BG_COLOR_MEDIUM, fg=FG_COLOR).pack(side="left", padx=5, pady=5)

        ping_frame = tk.Frame(self.button_frame, bg=BG_COLOR_DARK)
        ping_frame.pack(side="right", padx=10)
        tk.Label(ping_frame, text="Ping Aralığı:", bg=BG_COLOR_DARK, fg=FG_COLOR).pack(side="left", padx=(0, 5))
        
        self.ping_interval_var = tk.StringVar()
        self.ping_interval_combobox = ttk.Combobox(
            ping_frame,
            textvariable=self.ping_interval_var,
            values=list(PING_OPTIONS.keys()),
            state="readonly"
        )
        self.ping_interval_combobox.pack(side="left")
        self.ping_interval_combobox.set("5 Dakika")
        self.ping_interval_combobox.bind("<<ComboboxSelected>>", self.update_ping_interval)

        self.main_frame = tk.Frame(root, bg=BG_COLOR_DARK)
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan_map)
        self.canvas.bind("<MouseWheel>", self.zoom)

        self.pan_start = None
        self.device_list_panel = DeviceListPanel(self.main_frame, self)
        
        self.root.update()
        self.load_map(initial_load=True)

    def update_ping_interval(self, event=None):
        selected_option = self.ping_interval_var.get()
        new_interval = PING_OPTIONS.get(selected_option, PING_INTERVAL_SECONDS)
        
        if self.ping_interval != new_interval:
            self.ping_interval = new_interval
            for device in self.devices:
                device.set_ping_interval(self.ping_interval)

    def on_resize(self, event):
        if self.original_image:
            self.load_map_to_fit()

    def load_map(self, initial_load=False, file_path=None):
        if not file_path:
            file_path = "ALTINOVA ATÖLYE ALANLARI - 2025.png" if initial_load else filedialog.askopenfilename()
        
        if not file_path:
            return

        self.map_file_path = file_path
        try:
            self.original_image = Image.open(self.map_file_path)
            
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

        except FileNotFoundError:
            messagebox.showerror("Hata", "Harita dosyası bulunamadı. Lütfen dosya yolunu kontrol edin.")
            self.map_file_path = None
        except Exception as e:
            messagebox.showerror("Hata", f"Harita yüklenemedi: {e}")

    def load_map_to_fit(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
            
        img_width, img_height = self.original_image.size
        
        ratio = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)

        # 👇 ÖNCEKİ BOYUTLA AYNIYSA TEKRAR BOYUTLANDIRMA!
        if (hasattr(self, '_last_resized_size') and 
            self._last_resized_size == (new_width, new_height)):
            pass
        else:
            self.image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)
            self._last_resized_size = (new_width, new_height)

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
        if not self.original_image:
            return

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

        AddDeviceForm(self.root, self.on_form_submit)

    def on_form_submit(self, device_data):
        self.pending_device_data = device_data
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
        
        # Ping worker'a ekle
        self.ping_worker.devices_to_check.append(new_device)
        
    def save_project(self):
        if not self.map_file_path:
            messagebox.showerror("Hata", "Lütfen önce bir harita yükleyin.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        devices_data = []
        for device in self.devices:
            devices_data.append({
                "name": device.name,
                "ip": device.ip,
                "x": device.original_x,
                "y": device.original_y,
                "device_type": device.device_type,
                "model": device.model,
                "connected_port": device.connected_port,
                "starting_port": device.starting_port
            })

        project_data = {
            "map_path": self.map_file_path,
            "devices": devices_data
        }

        try:
            with open(file_path, "w") as f:
                json.dump(project_data, f, indent=4)
            messagebox.showinfo("Bilgi", "Proje başarıyla kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Projeyi kaydederken bir hata oluştu: {e}")

    def load_project(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                project_data = json.load(f)

            for device in self.devices:
                device.delete_device()
            self.devices.clear()
            self.device_list_panel.clear_listbox()

            map_path = project_data.get("map_path")
            if map_path and os.path.exists(map_path):
                self.load_map(file_path=map_path)
            elif map_path and not os.path.exists(map_path):
                messagebox.showwarning("Harita Bulunamadı", f"Projeye ait harita dosyası bulunamadı:\n{map_path}\n\nCihazlar yine de yüklenecek ancak harita gösterilemeyecek.")
                self.image = None
                self.original_image = None
                self.photo = None
                if self.image_id:
                    self.canvas.delete(self.image_id)
                self.image_id = None
            else:
                messagebox.showerror("Hata", "Kayıtlı harita yolu bulunamadı.")
                return

            devices_data = project_data.get("devices", [])
            for data in devices_data:
                new_device = Device(
                    self.canvas,
                    self,
                    data.get("name"),
                    data.get("ip"),
                    data.get("x"),
                    data.get("y"),
                    data.get("device_type"),
                    data.get("model"),
                    data.get("connected_port"),
                    data.get("starting_port")
                )
                self.devices.append(new_device)
                self.device_list_panel.add_device_to_list(new_device)
                
            # Ping worker'a tüm cihazları ekle
            self.ping_worker.devices_to_check.extend(self.devices)
                
            self.device_list_panel.update_device_list()
            messagebox.showinfo("Bilgi", "Proje başarıyla yüklendi.")
            
        except FileNotFoundError:
            messagebox.showerror("Hata", f"Dosya bulunamadı: {file_path}")
        except json.JSONDecodeError:
            messagebox.showerror("Hata", "Seçilen dosya geçerli bir JSON formatında değil.")
        except Exception as e:
            messagebox.showerror("Hata", f"Projeyi yüklerken bir hata oluştu: {e}")
            
    def set_selected_device(self, device):
        self.selected_device = device
        if self.selected_device:
            self.ping_button.config(state="normal")
        else:
            self.ping_button.config(state="disabled")

    def ping_selected_device(self):
        if self.selected_device:
            self.selected_device.ping_with_terminal()
