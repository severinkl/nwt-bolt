import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from config import AUTO_PROGRESS_TIMEOUT
import threading
import subprocess
from config.device_roles import DEVICE_ROLE_MAP


class ScenarioSelector:
    ADMIN_PIN = "1235"
    DEFAULT_IMAGE = "images/fhstp_logo.png"
    PROJECT_PATH = "/opt/sepnwt/nwt-packet-visualization-main"

    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.root = tk.Tk()
        self.root.title("Network Packet Simulator")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Left>", lambda e: self.previous_step())
        self.root.bind("<Right>", lambda e: self.next_step())
        self.root.bind("<Return>", lambda e: self.toggle_auto_progress())

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.current_scenario = None
        self.current_step = 0
        self.prev_step = -1
        self.scenario_handler = None
        self.auto_progress = False
        self.auto_progress_job = None
        self.admin_frame = None

        self.root.after(3000, lambda: self.root.attributes("-fullscreen", True))

        self.setup_styles()
        self.setup_ui()
        self.root.after(200, self.force_full_layout)
        self.poll_status_loop()

    def setup_styles(self):
        style = ttk.Style()
        style.configure(".", background="#ffffff", foreground="#005097")
        style.configure("Title.TLabel", font=('Helvetica', 24, 'bold'), padding=20)
        style.configure("Scenario.TButton", font=('Helvetica', 12), padding=10)
        style.configure("Control.TButton", font=('Helvetica', 18), padding=25)
        style.configure("Exit.TButton", font=('Helvetica', 10, 'bold'), padding=10)
        style.configure("Step.TLabel", font=('Helvetica', 12))
        style.configure("Main.TFrame", background="#ffffff")
        style.configure("Admin.TButton", font=('Helvetica', 16), padding=10)
        style.configure("AdminHeader.TLabel", font=('Helvetica', 18, 'bold'))
        style.configure("AdminCell.TLabel", font=('Helvetica', 14))

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root, padding="20", style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.setup_scenario_selector()
        self.setup_scenario_view()

    def setup_scenario_selector(self):
        self.scenario_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.scenario_frame.grid(row=0, column=0, sticky="nsew")

        self.scenario_frame.columnconfigure(0, weight=1)
        self.scenario_frame.columnconfigure(1, weight=1)

        ttk.Label(self.scenario_frame, text="Network Packet Simulator",
          font=('Helvetica', 28, 'bold')).grid(row=0, column=0, columnspan=2, pady=(20, 10), sticky="n")

        # Statusbereich (links oben im Szenario-Label)
        status_frame = ttk.Frame(self.scenario_frame, style="Main.TFrame", padding=5)
        status_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        ttk.Label(status_frame, text="Name", font=("Helvetica", 16, "bold")).grid(row=0, column=0, padx=5)
        ttk.Label(status_frame, text="Status", font=("Helvetica", 16, "bold")).grid(row=0, column=1, padx=5)
        ttk.Label(status_frame, text="Role", font=("Helvetica", 16, "bold")).grid(row=0, column=2, padx=5)

        self.status_labels = {}
        from config.rpi_status_config import RPI_HOSTS
        for i, (name, ip) in enumerate(RPI_HOSTS.items(), start=1):
            ttk.Label(status_frame, text=name, font=("Helvetica", 11)).grid(row=i, column=0, padx=5, pady=2, sticky="w")
            status_label = ttk.Label(status_frame, text="...", font=("Helvetica", 11))
            status_label.grid(row=i, column=1, padx=5, pady=2)
            role_label = ttk.Label(status_frame, text="...", font=("Helvetica", 11))
            role_label.grid(row=i, column=2, padx=5, pady=2)
            self.status_labels[name] = (status_label, role_label, ip)

        # Logo (Admin-Zugang nach 5 Klicks)
        self.admin_clicks = 0
        logo_image = Image.open("images/fhstp_logo.png").resize((60, 80), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_image)

        logo_label = ttk.Label(self.scenario_frame, image=self.logo_photo)
        logo_label.image = self.logo_photo
        logo_label.grid(row=0, column=1, sticky=tk.NE, padx=5, pady=5)
        logo_label.bind("<Button-1>", self.handle_logo_click)

        # Szenarien mittig platzieren
        button_frame = ttk.Frame(self.scenario_frame, style="Main.TFrame")
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky="n")

        ttk.Label(button_frame, text="Wähle ein Szenario:", font=("Helvetica", 24, "bold")).grid(
            row=0, column=0, pady=(0, 10), sticky="n"
        )

        scenarios = [
            ("HTTP (ORF) Level 1", "http_level_1"),
            ("HTTP (ORF) Level 2", "http_level_2"),
            # ("HTTP (ORF) Level 3", "http_level_3")
        ]

        for idx, (name, scenario_id) in enumerate(scenarios, start=1):
            self.create_button(button_frame, name, lambda s=scenario_id: self.start_scenario(s),
                            style="Control.TButton").grid(
                row=idx, column=0, pady=5, padx=40, sticky="ew"
            )

        threading.Thread(target=self.update_all_statuses, daemon=True).start()

    def handle_logo_click(self, event):
        self.admin_clicks += 1
        if self.admin_clicks >= 5:
            self.admin_clicks = 0
            self.show_pin_prompt()

    def update_all_statuses(self):
        for name, (status_label, role_label, ip) in self.status_labels.items():
            threading.Thread(
                target=self.update_device_status,
                args=(status_label, role_label, ip),
                daemon=True
            ).start()

    def setup_scenario_view(self):
        self.view_frame = ttk.Frame(self.main_frame, style="Main.TFrame")

        self.create_button(self.view_frame, "←", self.exit_scenario, style="Exit.TButton", width=3).grid(
            row=0, column=0, sticky=tk.NW, padx=5, pady=5
        )

        image_container = ttk.Frame(self.view_frame, style="Main.TFrame")
        image_container.grid(row=1, column=0, sticky="nsew", pady=(10, 10))
        image_container.rowconfigure(0, weight=1)
        image_container.columnconfigure(0, weight=1)

        self.image_label = ttk.Label(image_container, anchor="center")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        self.view_frame.rowconfigure(1, weight=1)
        self.view_frame.columnconfigure(0, weight=1)

        step_frame = ttk.Frame(self.view_frame, style="Main.TFrame")
        step_frame.grid(row=2, column=0, pady=(10, 40), sticky="ew")
        for i in range(3):
            step_frame.columnconfigure(i, weight=1)

        self.prev_btn = self.create_button(step_frame, "Previous", self.previous_step, state=tk.DISABLED)
        self.prev_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.auto_btn = self.create_button(step_frame, "Start Auto", self.toggle_auto_progress)
        self.auto_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.restart_btn = self.create_button(step_frame, "Restart", self.restart_scenario)
        self.restart_btn.grid(row=0, column=1, padx=5, sticky="ew")
        self.restart_btn.grid_remove()  # Hide initially

        self.next_btn = self.create_button(step_frame, "Next", self.next_step, state=tk.DISABLED)
        self.next_btn.grid(row=0, column=2, padx=5, sticky="ew")

        self.step_label = ttk.Label(step_frame, text="Step: 0 / 0", style="Step.TLabel")
        self.step_label.grid(row=1, column=0, columnspan=3, pady=10)

    def create_button(self, parent, text, command, style="Scenario.TButton", **kwargs):
        return ttk.Button(parent, text=text, command=command, style=style, **kwargs)

    def force_full_layout(self):
        self.main_frame.grid_propagate(True)
        self.scenario_frame.grid_propagate(True)

    def toggle_auto_progress(self):
        if not self.current_scenario:
            return
        if self.auto_progress:
            self.stop_auto_progress()
        else:
            self.start_auto_progress()

    def start_auto_progress(self):
        self.auto_progress = True
        self.auto_btn.config(text="Stop Auto")
        self.next_step()
        self.schedule_next_step()

    def stop_auto_progress(self):
        self.auto_progress = False
        self.auto_btn.config(text="Start Auto")
        if self.auto_progress_job:
            self.root.after_cancel(self.auto_progress_job)
            self.auto_progress_job = None

    def schedule_next_step(self):
        if self.auto_progress and self.current_step < self.scenario_handler.maximum_steps - 1:
            self.auto_progress_job = self.root.after(AUTO_PROGRESS_TIMEOUT, self.auto_step)
        else:
            self.stop_auto_progress()

    def auto_step(self):
        self.next_step()
        self.schedule_next_step()

    def restart_scenario(self):
        self.current_step = 0
        self.state_manager.update_state({"scenario": self.current_scenario, "step": 0})
        self.update_controls()
        self.update_image()

    def start_scenario(self, scenario_id):
        try:
            self.scenario_handler = self.state_manager.load_scenario(scenario_id)
        except Exception as e:
            print(f"Fehler beim Laden des Szenarios: {e}")
            return

        self.current_scenario = scenario_id
        self.current_step = 0
        self.prev_step = -1
        self.state_manager.update_state({"scenario": scenario_id, "step": 0})

        self.scenario_frame.grid_remove()
        self.view_frame.grid(row=0, column=0, sticky="nsew")
        self.update_controls()
        self.update_image()

    def exit_scenario(self):
        if self.auto_progress:
            self.stop_auto_progress()

        self.current_scenario = None
        self.current_step = 0
        self.scenario_handler = None

        self.view_frame.grid_remove()
        self.scenario_frame.grid()
        self.update_display(self.DEFAULT_IMAGE)
        self.state_manager.update_state({"scenario": "", "step": 0})

    def next_step(self):
        if self.current_step < self.scenario_handler.maximum_steps - 1:
            self.current_step += 1
            self.update_state_and_view()

    def previous_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_state_and_view()

    def update_state_and_view(self):
        self.state_manager.update_state({"scenario": self.current_scenario, "step": self.current_step})
        self.update_controls()
        self.update_image()

    def update_controls(self):
        if not self.scenario_handler:
            return

        is_last_step = self.current_step >= self.scenario_handler.maximum_steps - 1
        self.next_btn.config(state=tk.NORMAL if not is_last_step else tk.DISABLED)
        self.prev_btn.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        self.step_label.config(text=f"Step: {self.current_step + 1} / {self.scenario_handler.maximum_steps}")

        # Toggle visibility of auto/restart buttons based on step
        if is_last_step:
            self.auto_btn.grid_remove()
            self.restart_btn.grid()
        else:
            self.restart_btn.grid_remove()
            self.auto_btn.grid()

    def scale_image(self, image):
        self.root.update_idletasks()
        label_width = self.image_label.winfo_width() or 800
        label_height = self.image_label.winfo_height() or 600
        scale_ratio = min(label_width / image.width, label_height / image.height)
        return image.resize((int(image.width * scale_ratio), int(image.height * scale_ratio)), Image.Resampling.BILINEAR)

    def update_image(self):
        if self.scenario_handler:
            result = self.scenario_handler.execute_step(self.current_step)
            
            # Handle different result types
            if isinstance(result, dict):
                if result["type"] == "text":
                    self.display_text(result["content"])
                elif result["type"] == "image_with_text":
                    self.display_image_with_text(result["image"], result["text"])
                elif result["type"] == "image":
                    threading.Thread(target=self.load_and_display_image, args=(result["content"],)).start()
            else:
                # Backward compatibility for old string returns
                if result and result.startswith("TEXT:"):
                    text_content = result[5:]  # Remove "TEXT:" prefix
                    self.display_text(text_content)
                else:
                    threading.Thread(target=self.load_and_display_image, args=(result,)).start()

    def load_and_display_image(self, image_path):
        try:
            image = Image.open(image_path)
            scaled_image = self.scale_image(image)
            photo = ImageTk.PhotoImage(scaled_image)
            self.root.after(0, lambda: self.set_image(photo))
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

    def set_image(self, photo):
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def update_display(self, image_path):
        threading.Thread(target=self.load_and_display_image, args=(image_path,)).start()

    def display_text(self, text_content):
        """Display text instead of an image"""
        try:
            # Clear any existing image
            self.image_label.configure(image="")
            self.image_label.image = None
            
            # Configure label for text display
            self.image_label.configure(
                text=text_content,
                font=('Helvetica', 36, 'bold'),
                foreground='#005097',
                background='#ffffff',
                wraplength=800,
                justify='center',
                anchor='center'
            )
        except Exception as e:
            print(f"Error displaying text: {e}")

    def display_image_with_text(self, image_path, text_content):
        """Display text above an image in the scenario selector"""
        try:
            # Clear any existing image
            self.image_label.configure(image="", text="")
            self.image_label.image = None
            
            # Create a frame to hold both text and image
            if hasattr(self, 'content_frame'):
                self.content_frame.destroy()
                
            # Get the parent of image_label to place our content frame
            parent = self.image_label.master
            
            self.content_frame = ttk.Frame(parent, style="Main.TFrame")
            self.content_frame.grid(row=0, column=0, sticky="nsew")
            self.content_frame.rowconfigure(1, weight=1)
            self.content_frame.columnconfigure(0, weight=1)
            
            # Add text label at the top
            text_label = ttk.Label(
                self.content_frame,
                text=text_content,
                font=('Helvetica', 36, 'bold'),
                foreground='#005097',
                background='#ffffff',
                wraplength=800,
                justify='center',
                anchor='center'
            )
            text_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")
            
            # Add image label below
            image_label = ttk.Label(self.content_frame, anchor="center")
            image_label.grid(row=1, column=0, sticky="nsew")
            
            # Load and display the image
            def load_image():
                try:
                    image = Image.open(image_path)
                    scaled_image = self.scale_image(image)
                    photo = ImageTk.PhotoImage(scaled_image)
                    self.root.after(0, lambda: self.set_combined_image(image_label, photo))
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
            
            threading.Thread(target=load_image).start()
            
        except Exception as e:
            print(f"Error displaying image with text: {e}")
            # Fallback to just showing the image
            threading.Thread(target=self.load_and_display_image, args=(image_path,)).start()
    
    def set_combined_image(self, image_label, photo):
        """Set image in the combined display"""
        image_label.configure(image=photo)
        image_label.image = photo

    def show_pin_prompt(self):
        self.pin_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.pin_entry_value = tk.StringVar()

        self.pin_frame.columnconfigure(0, weight=1)
        self.pin_frame.columnconfigure(1, weight=2)
        self.pin_frame.columnconfigure(2, weight=1)

        self.create_button(self.pin_frame, "×", self.back_to_selector, style="Exit.TButton", width=3).grid(
            row=0, column=0, sticky="nw", padx=10, pady=10
        )

        ttk.Entry(self.pin_frame, textvariable=self.pin_entry_value, show="*", font=("Helvetica", 36),
                justify="center").grid(row=1, column=1, pady=(10, 30), sticky="ew", padx=80)

        button_container = ttk.Frame(self.pin_frame, style="Main.TFrame")
        button_container.grid(row=2, column=1, pady=(0, 40))

        buttons = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['←', '0', 'OK']
        ]

        for r, row in enumerate(buttons):
            for c, char in enumerate(row):
                tk.Button(button_container, text=char, font=("Helvetica", 24), width=4, height=2,
                        command=lambda c=char: self.handle_pin_button(c)).grid(row=r, column=c, padx=10, pady=10)

        for i in range(3):
            button_container.grid_columnconfigure(i, weight=1)

        self.scenario_frame.grid_remove()
        self.pin_frame.grid(row=0, column=0, sticky="nsew")

    def handle_pin_button(self, value):
        if value == '←':
            self.pin_entry_value.set(self.pin_entry_value.get()[:-1])
        elif value == 'OK':
            if self.pin_entry_value.get() == self.ADMIN_PIN:
                self.pin_frame.grid_remove()
                self.show_admin_frame()
            else:
                self.pin_entry_value.set("")
        else:
            self.pin_entry_value.set(self.pin_entry_value.get() + value)

    def back_to_selector(self):
        if hasattr(self, 'pin_frame') and self.pin_frame:
            self.pin_frame.destroy()
            self.pin_frame = None
        self.admin_clicks = 0
        self.setup_scenario_selector()

    def show_admin_frame(self):
        from config.rpi_status_config import RPI_HOSTS

        if self.admin_frame:
            self.admin_frame.destroy()
        self.admin_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.admin_frame.grid(row=0, column=0, sticky="nsew")

        self.admin_frame.columnconfigure(0, weight=1)
        self.admin_frame.rowconfigure(1, weight=1)

        ttk.Label(self.admin_frame, text="Admin Panel", font=("Helvetica", 28, "bold")).grid(
            row=0, column=0, pady=(20, 10)
        )

        table_frame = ttk.Frame(self.admin_frame, style="Main.TFrame")
        table_frame.grid(row=1, column=0, pady=20)

        headers = ["Name", "Status", "Role", "Reboot", "Shutdown", "Exit Program", "Typ", "Start"]
        for i, h in enumerate(headers):
            ttk.Label(table_frame, text=h, style="AdminHeader.TLabel").grid(row=0, column=i, padx=10, pady=5)

        self.admin_status_labels = {}
        for idx, (name, ip) in enumerate(RPI_HOSTS.items(), start=1):
            ttk.Label(table_frame, text=name, style="AdminCell.TLabel").grid(row=idx, column=0, padx=10, pady=5)

            status_label = ttk.Label(table_frame, text="...", font=("Helvetica", 12))
            status_label.grid(row=idx, column=1, padx=10, pady=5)
            role_label = ttk.Label(table_frame, text="...", font=("Helvetica", 12))
            role_label.grid(row=idx, column=2, padx=10, pady=5)
            self.admin_status_labels[name] = (status_label, role_label, ip)
            threading.Thread(
                target=self.update_device_status,
                args=(status_label, role_label, ip),
                daemon=True
            ).start()

            self.create_button(table_frame, "Reboot", lambda ip=ip: self.remote_reboot(ip), style="Admin.TButton")\
                .grid(row=idx, column=3, padx=5)

            self.create_button(table_frame, "Shutdown", lambda ip=ip: self.remote_shutdown(ip), style="Admin.TButton")\
                .grid(row=idx, column=4, padx=5)

            self.create_button(table_frame, "Exit", lambda ip=ip: self.remote_exit(ip), style="Admin.TButton")\
                .grid(row=idx, column=5, padx=5)

            device_types = ["router", "firewall", "server", "dns", "switch"]
            default_role = DEVICE_ROLE_MAP.get(name.lower(), device_types[0])
            device_type_var = tk.StringVar(value=default_role)
            dropdown = tk.OptionMenu(table_frame, device_type_var, *device_types)
            dropdown.config(width=10)
            dropdown.grid(row=idx, column=6, padx=5)

            self.create_button(table_frame, "Start", lambda ip=ip, dev_type=device_type_var: self.remote_start(ip, dev_type.get()), style="Admin.TButton").grid(row=idx, column=7, padx=5)

        self.create_button(self.admin_frame, "← Zurück", self.show_scenario_selector, style="Exit.TButton")\
            .grid(row=2, column=0, pady=20)

    def update_device_status(self, status_label, role_label, ip):
        from platform import system
        param = "-n" if system().lower() == "windows" else "-c"
        ping_command = ["ping", param, "1", ip]

        try:
            result = subprocess.call(ping_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            status = "✅" if result == 0 else "❌"
        except Exception:
            status = "❌"

        role = self.get_remote_role(ip)

        self.root.after(0, lambda: status_label.config(text=status))
        if role_label:
            self.root.after(0, lambda: role_label.config(text=role))

    def poll_status_loop(self):
        def ping_all():
            all_label_dicts = [self.status_labels]
            if hasattr(self, 'admin_status_labels'):
                all_label_dicts.append(self.admin_status_labels)

            for label_dict in all_label_dicts:
                for name, values in label_dict.items():
                    if len(values) == 3:
                        status_label, role_label, ip = values
                    else:
                        status_label, ip = values
                        role_label = None
                    threading.Thread(
                        target=self.update_device_status,
                        args=(status_label, role_label, ip),
                        daemon=True
                    ).start()

        ping_all()
        self.root.after(5000, self.poll_status_loop)

    def _run_ssh_command(self, ip, command, label):
        full_command = ["ssh", f"rpi@{ip}"] + command
        print(f"[INFO] {label} {ip}: {full_command}")
        try:
            subprocess.run(full_command, check=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[OK] {label} auf {ip} gesendet.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {label} fehlgeschlagen für {ip}: {e}")
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {label} Timeout auf {ip}")
        except Exception as e:
            print(f"[EXCEPTION] {label} auf {ip}: {e}")

    def remote_reboot(self, ip):
        threading.Thread(target=self._run_ssh_command, args=(ip, ["sudo", "reboot"], "Reboot"), daemon=True).start()

    def remote_shutdown(self, ip):
        threading.Thread(target=self._run_ssh_command, args=(ip, ["sudo", "shutdown", "now"], "Shutdown"), daemon=True).start()

    def remote_exit(self, ip):
        threading.Thread(target=self._run_ssh_command, args=(ip, ["pkill", "-f", "main.py"], "Exit"), daemon=True).start()

    def remote_start(self, ip, device_type):
        cmd_str = f"cd {self.PROJECT_PATH} && DISPLAY=:0 python3 main.py {device_type}"
        full_command = ["ssh", f"rpi@{ip}", cmd_str]
        print(f"[INFO] SSH Befehl: {' '.join(full_command)}")
        threading.Thread(
            target=subprocess.run,
            args=(full_command,),
            kwargs={"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL},
            daemon=True
        ).start()

    def get_remote_role(self, ip):
        try:
            # Prüfe, ob main.py läuft (nicht erreichbar = no role)
            check_cmd = ["ssh", "-o", "StrictHostKeyChecking=accept-new", f"rpi@{ip}", "pgrep", "-f", "main.py"]
            result = subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)

            if result.returncode != 0:
                return "no role"

            # Wenn main.py läuft, extrahiere Argument
            command = (
                "ps aux | grep '[m]ain.py' | grep -v 'ssh' | awk '{for(i=11;i<=NF;i++) "
                "if($i ~ /main\\.py/) { if((i+1)<=NF && $(i+1) !~ /^-/ && $(i+1) != \"\") "
                "print $(i+1); else print \"\"; break }}'"
            )
            role = subprocess.check_output(
                ["ssh", "-o", "StrictHostKeyChecking=accept-new", f"rpi@{ip}", command],
                stderr=subprocess.DEVNULL,
                timeout=3
            ).decode("utf-8").strip()

            # Wenn kein Argument → nutze Hostname
            if not role:
                hostname_cmd = ["ssh", "-o", "StrictHostKeyChecking=accept-new", f"rpi@{ip}", "hostname"]
                hostname = subprocess.check_output(
                    hostname_cmd,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                ).decode("utf-8").strip()

                return DEVICE_ROLE_MAP.get(hostname.lower(), "no role")

            return role
        except Exception:
            return "no role"


    def show_scenario_selector(self):
        if self.admin_frame:
            self.admin_frame.grid_remove()
        self.scenario_frame.grid()

    def run(self):
        self.root.mainloop()
