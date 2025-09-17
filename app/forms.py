# forms.py

import tkinter as tk
from tkinter import messagebox
from .config import *

class EditDeviceForm(tk.Toplevel):
    def __init__(self, parent, device):
        super().__init__(parent)
        self.device = device
        self.title("Cihazı Düzenle")
        self.geometry("350x300")
        self.configure(bg=BG_COLOR_DARK)

        self.update_idletasks()
        
        form_frame = tk.Frame(self, bg=BG_COLOR_DARK)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        fields = [
            ("Cihaz Adı:", "name_entry", self.device.name),
            ("IP Adresi:", "ip_entry", self.device.ip),
            ("Tür (Opsiyonel):", "type_entry", self.device.device_type),
            ("Model (Opsiyonel):", "model_entry", self.device.model),
            ("Bağlı Olduğu Port (Opsiyonel):", "connected_port_entry", self.device.connected_port),
            ("Başlangıç Portu (Opsiyonel):", "starting_port_entry", self.device.starting_port),
        ]
        
        for text, entry_name, value in fields:
            label = tk.Label(form_frame, text=text, bg=BG_COLOR_DARK, fg=FG_COLOR, font=FONT_DEFAULT)
            label.pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(form_frame, bg=BG_COLOR_MEDIUM, fg=FG_COLOR, insertbackground=FG_COLOR)
            entry.insert(0, value)
            setattr(self, entry_name, entry)
            entry.pack(fill="x", pady=(0, 5))

        button_frame = tk.Frame(self, bg=BG_COLOR_DARK)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Kaydet", command=self.on_save, bg=BUTTON_COLOR_ADD, fg=FG_COLOR).pack(side="left", padx=10)
        tk.Button(button_frame, text="Vazgeç", command=self.destroy, bg=BUTTON_COLOR_CANCEL, fg=FG_COLOR).pack(side="right", padx=10)

    def on_save(self):
        new_name = self.name_entry.get()
        new_ip = self.ip_entry.get()
        new_type = self.type_entry.get()
        new_model = self.model_entry.get()
        new_connected_port = self.connected_port_entry.get()
        new_starting_port = self.starting_port_entry.get()
        
        if new_name and new_ip:
            self.device.name = new_name
            self.device.ip = new_ip
            self.device.device_type = new_type
            self.device.model = new_model
            self.device.connected_port = new_connected_port
            self.device.starting_port = new_starting_port

            self.device.canvas.itemconfigure(self.device.label, text=new_name)
            self.device.app.device_list_panel.update_device_list()
            self.destroy()
        else:
            messagebox.showerror("Hata", "Lütfen Cihaz Adı ve IP Adresi alanlarını doldurun.")

class DeviceForm(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.title("Cihaz Ekle")
        self.geometry("350x300")
        self.configure(bg=BG_COLOR_DARK)

        self.update_idletasks()

        form_frame = tk.Frame(self, bg=BG_COLOR_DARK)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        fields = [
            ("Cihaz Adı:", "name_entry"),
            ("IP Adresi:", "ip_entry"),
            ("Tür (Opsiyonel):", "type_entry"),
            ("Model (Opsiyonel):", "model_entry"),
            ("Bağlı Olduğu Port (Opsiyonel):", "connected_port_entry"),
            ("Başlangıç Portu (Opsiyonel):", "starting_port_entry"),
        ]
        
        for text, entry_name in fields:
            label = tk.Label(form_frame, text=text, bg=BG_COLOR_DARK, fg=FG_COLOR, font=FONT_DEFAULT)
            label.pack(anchor="w", pady=(5, 0))
            entry = tk.Entry(form_frame, bg=BG_COLOR_MEDIUM, fg=FG_COLOR, insertbackground=FG_COLOR)
            setattr(self, entry_name, entry)
            entry.pack(fill="x", pady=(0, 5))

        button_frame = tk.Frame(self, bg=BG_COLOR_DARK)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Ekle", command=self.on_add, bg=BUTTON_COLOR_ADD, fg=FG_COLOR).pack(side="left", padx=10)
        tk.Button(button_frame, text="Vazgeç", command=self.destroy, bg=BUTTON_COLOR_CANCEL, fg=FG_COLOR).pack(side="right", padx=10)

    def on_add(self):
        name = self.name_entry.get()
        ip = self.ip_entry.get()
        device_type = self.type_entry.get()
        model = self.model_entry.get()
        connected_port = self.connected_port_entry.get()
        starting_port = self.starting_port_entry.get()
        
        if name and ip:
            self.callback(name, ip, device_type, model, connected_port, starting_port)
            self.destroy()
        else:
            messagebox.showerror("Hata", "Lütfen Cihaz Adı ve IP Adresi alanlarını doldurun.")