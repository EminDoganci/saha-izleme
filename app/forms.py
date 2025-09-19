# forms.py

import tkinter as tk
from tkinter import ttk, messagebox
import ipaddress

class AddDeviceForm(tk.Toplevel):
    def __init__(self, parent, on_submit):
        super().__init__(parent)
        self.parent = parent
        self.on_submit = on_submit
        self.title("Yeni Cihaz Ekle")
        self.geometry("300x400")
        self.resizable(False, False)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        # Name
        ttk.Label(main_frame, text="Cihaz Adı:").pack(fill="x", pady=2)
        self.name_entry = ttk.Entry(main_frame)
        self.name_entry.pack(fill="x", pady=2)

        # IP
        ttk.Label(main_frame, text="IP Adresi:").pack(fill="x", pady=2)
        self.ip_entry = ttk.Entry(main_frame)
        self.ip_entry.pack(fill="x", pady=2)
        
        # Device Type
        ttk.Label(main_frame, text="Cihaz Tipi:").pack(fill="x", pady=2)
        self.device_type_combobox = ttk.Combobox(main_frame, values=["Router", "Switch", "Server", "Bilgisayar", "Yazıcı", "Diğer"])
        self.device_type_combobox.pack(fill="x", pady=2)
        self.device_type_combobox.current(0)

        # Model
        ttk.Label(main_frame, text="Model:").pack(fill="x", pady=2)
        self.model_entry = ttk.Entry(main_frame)
        self.model_entry.pack(fill="x", pady=2)

        # Connected Port
        ttk.Label(main_frame, text="Bağlı Olduğu Port:").pack(fill="x", pady=2)
        self.connected_port_entry = ttk.Entry(main_frame)
        self.connected_port_entry.pack(fill="x", pady=2)

        # Starting Port
        ttk.Label(main_frame, text="Başlangıç Portu:").pack(fill="x", pady=2)
        self.starting_port_entry = ttk.Entry(main_frame)
        self.starting_port_entry.pack(fill="x", pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        add_button = ttk.Button(button_frame, text="Ekle", command=self.add_device)
        add_button.pack(side="left", expand=True, padx=5)

        cancel_button = ttk.Button(button_frame, text="İptal", command=self.destroy)
        cancel_button.pack(side="right", expand=True, padx=5)

    def add_device(self):
        name = self.name_entry.get().strip()
        ip = self.ip_entry.get().strip()
        device_type = self.device_type_combobox.get().strip()
        model = self.model_entry.get().strip()
        connected_port = self.connected_port_entry.get().strip()
        starting_port = self.starting_port_entry.get().strip()

        if not name or not ip:
            messagebox.showerror("Hata", "Cihaz Adı ve IP Adresi boş bırakılamaz.", parent=self)
            return

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz IP adresi formatı.", parent=self)
            return

        device_data = {
            "name": name,
            "ip": ip,
            "device_type": device_type,
            "model": model,
            "connected_port": connected_port,
            "starting_port": starting_port,
        }

        self.on_submit(device_data)
        self.destroy()

class EditDeviceForm(tk.Toplevel):
    def __init__(self, parent, device): 
        super().__init__(parent)
        self.parent = parent
        self.device = device
        self.title(f"'{device.name}' Cihazını Düzenle")
        self.geometry("300x400")
        self.resizable(False, False)
        self.grab_set()

        self.create_widgets()
        self.load_device_data()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        # Name
        ttk.Label(main_frame, text="Cihaz Adı:").pack(fill="x", pady=2)
        self.name_entry = ttk.Entry(main_frame)
        self.name_entry.pack(fill="x", pady=2)

        # IP
        ttk.Label(main_frame, text="IP Adresi:").pack(fill="x", pady=2)
        self.ip_entry = ttk.Entry(main_frame)
        self.ip_entry.pack(fill="x", pady=2)
        
        # Device Type
        ttk.Label(main_frame, text="Cihaz Tipi:").pack(fill="x", pady=2)
        self.device_type_combobox = ttk.Combobox(main_frame, values=["Router", "Switch", "Server", "Bilgisayar", "Yazıcı", "Diğer"])
        self.device_type_combobox.pack(fill="x", pady=2)

        # Model
        ttk.Label(main_frame, text="Model:").pack(fill="x", pady=2)
        self.model_entry = ttk.Entry(main_frame)
        self.model_entry.pack(fill="x", pady=2)

        # Connected Port
        ttk.Label(main_frame, text="Bağlı Olduğu Port:").pack(fill="x", pady=2)
        self.connected_port_entry = ttk.Entry(main_frame)
        self.connected_port_entry.pack(fill="x", pady=2)

        # Starting Port
        ttk.Label(main_frame, text="Başlangıç Portu:").pack(fill="x", pady=2)
        self.starting_port_entry = ttk.Entry(main_frame)
        self.starting_port_entry.pack(fill="x", pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        save_button = ttk.Button(button_frame, text="Kaydet", command=self.save_changes)
        save_button.pack(side="left", expand=True, padx=5)

        cancel_button = ttk.Button(button_frame, text="İptal", command=self.destroy)
        cancel_button.pack(side="right", expand=True, padx=5)
        
    def load_device_data(self):
        self.name_entry.insert(0, self.device.name)
        self.ip_entry.insert(0, self.device.ip)
        self.device_type_combobox.set(self.device.device_type)
        self.model_entry.insert(0, self.device.model)
        self.connected_port_entry.insert(0, self.device.connected_port)
        self.starting_port_entry.insert(0, self.device.starting_port)

    def save_changes(self):
        new_name = self.name_entry.get().strip()
        new_ip = self.ip_entry.get().strip()
        new_device_type = self.device_type_combobox.get().strip()
        new_model = self.model_entry.get().strip()
        new_connected_port = self.connected_port_entry.get().strip()
        new_starting_port = self.starting_port_entry.get().strip()

        if not new_name or not new_ip:
            messagebox.showerror("Hata", "Cihaz Adı ve IP Adresi boş bırakılamaz.", parent=self)
            return

        try:
            ipaddress.ip_address(new_ip)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz IP adresi formatı.", parent=self)
            return

        self.device.name = new_name
        self.device.ip = new_ip
        self.device.device_type = new_device_type
        self.device.model = new_model
        self.device.connected_port = new_connected_port
        self.device.starting_port = new_starting_port

        self.device.app.device_list_panel.update_device_list()
        self.device.canvas.itemconfigure(self.device.label, text=new_name)
        
        self.destroy()
