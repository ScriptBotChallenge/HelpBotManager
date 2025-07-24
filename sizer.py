import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os
import threading
import win32gui
import win32process
import psutil
from autoclicker import AutoClicker


class ProcessManager:
    def __init__(self):
        self.root = tk.Tk()
        self.autoclicker = AutoClicker()
        self.exe_path = tk.StringVar()
        self.proc_map = {}
        self._setup_ui()

    def _setup_ui(self):
        self.root.title("Help bot manager [Doomsday.exe]")
        self.root.geometry("700x500")
        self.root.configure(bg="#1e1e1e")

        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background="#1e1e1e")

        style.configure("TLabel", foreground="white", background="#1e1e1e")
        style.configure("TButton", foreground="white", background="#2e2e2e",
                        padding=5, borderwidth=0, relief="flat")
        style.configure("TEntry", fieldbackground="#2e2e2e", foreground="white",
                        background="#1e1e1e")
        style.configure("TCombobox", fieldbackground="#2e2e2e", background="#1e1e1e",
                        foreground="white", padding=3, relief="flat")
        style.configure("Treeview", background="#2a2a2a", fieldbackground="#2a2a2a",
                        foreground="white", bordercolor="#1e1e1e")
        style.configure("Treeview.Heading", background="#2e2e2e", foreground="white")

        style.map("TButton", background=[("active", "#3a3a3a")],
                  foreground=[("active", "white")])
        style.map("TCombobox", fieldbackground=[('readonly', '#3a3a3a')])
        style.map("Treeview.Heading", background=[("active", "#2e2e2e")],
                  foreground=[("active", "white")])

    def _create_widgets(self):
        self.system_stats_label = ttk.Label(
            self.root, text="Загрузка системы: CPU 0%, RAM 0%",
            anchor="center", style="TLabel"
        )
        self.system_stats_label.pack(pady=5)

        self._create_top_frame()
        self._create_main_frame()
        self._create_bottom_frame()

    def _create_top_frame(self):
        top_frame = ttk.Frame(self.root, style="Dark.TFrame")
        top_frame.pack(fill="x", pady=5, padx=10)

        self.entry = ttk.Entry(top_frame, textvariable=self.exe_path, width=50)
        self.entry.pack(side=tk.LEFT)

        ttk.Button(top_frame, text="Выбрать .exe",
                   command=self._select_exe).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Запустить окно",
                   command=self._launch_game).pack(side=tk.LEFT, padx=10)

    def _create_main_frame(self):
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10)

        self.tree = ttk.Treeview(main_frame, columns=("hwnd", "ram"),
                                 show="headings", height=15)
        self.tree.heading("hwnd", text="HWND")
        self.tree.heading("ram", text="RAM MB")
        self.tree.column("ram", width=100, anchor="center")
        self.tree.column("hwnd", width=150)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        self._create_side_controls(main_frame)

    def _create_side_controls(self, parent):
        side_controls = ttk.Frame(parent, style="Dark.TFrame")
        side_controls.pack(side=tk.RIGHT, fill="y", padx=10)

        ttk.Label(side_controls, text="Управление выделенным окном").pack(anchor="w")

        self.single_resize_combo = ttk.Combobox(
            side_controls, values=["800x600", "640x480", "320x240"], width=10
        )
        self.single_resize_combo.set("800x600")
        self.single_resize_combo.pack(pady=5)

        ttk.Button(side_controls, text="Применить",
                   command=self._apply_resize).pack(fill="x", pady=2)
        ttk.Button(side_controls, text="Закрыть окно",
                   command=self._apply_close).pack(fill="x", pady=2)
        ttk.Button(side_controls, text="Закрыть все окна",
                   command=self._close_all_windows).pack(fill="x", pady=2)

        self._create_autoclicker_controls(side_controls)

    def _create_autoclicker_controls(self, parent):
        ttk.Label(parent, text="Управление Ручками").pack(anchor="w", pady=(15, 0))

        self.ruchki_status = ttk.Label(parent, text="Статус: Неактивно", foreground="gray")
        self.ruchki_status.pack(anchor="w", pady=(0, 5))

        ttk.Button(parent, text="Старт", command=self._start_autoclicker).pack(fill="x", pady=2)
        ttk.Button(parent, text="Выбрать область",
                   command=lambda: self.autoclicker.select_area(self.root)).pack(fill="x", pady=2)
        ttk.Button(parent, text="Стоп", command=self._stop_autoclicker).pack(fill="x", pady=2)

    def _create_bottom_frame(self):
        bottom_frame = ttk.Frame(self.root, style="Dark.TFrame")
        bottom_frame.pack(fill="x", pady=10, padx=10)

        left_frame = ttk.Frame(bottom_frame, style="Dark.TFrame")
        left_frame.pack(side=tk.LEFT, fill="x", expand=True)

        right_frame = ttk.Frame(bottom_frame, style="Dark.TFrame")
        right_frame.pack(side=tk.RIGHT)

        ttk.Label(left_frame, text="Изменить размер всех окон:").pack(side=tk.LEFT)

        self.resize_all_combo = ttk.Combobox(
            left_frame, values=["800x600", "640x480", "320x240"], width=10
        )
        self.resize_all_combo.set("800x600")
        self.resize_all_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(left_frame, text="Применить ко всем",
                   command=self._resize_all).pack(side=tk.LEFT, padx=10)

        link_label = tk.Label(right_frame, text="t.me/doomsday_script",
                              fg="skyblue", cursor="hand2", bg="#1e1e1e")
        link_label.pack(side=tk.RIGHT)
        link_label.bind("<Button-1>",
                        lambda e: os.system("start https://t.me/doomsday_script"))

    def _get_doomsday_windows(self):
        hwnds = []

        def enum_callback(hwnd, _):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                if (proc.name().lower() == "doomsday.exe" and
                        win32gui.IsWindowVisible(hwnd)):
                    hwnds.append(hwnd)
            except:
                pass

        win32gui.EnumWindows(enum_callback, None)
        return hwnds

    def _resize_window(self, hwnd, width, height):
        try:
            x, y, _, _ = win32gui.GetWindowRect(hwnd)
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
        except:
            pass

    def _close_window(self, hwnd):
        try:
            win32gui.PostMessage(hwnd, 0x0010, 0, 0)
        except:
            pass

    def _select_exe(self):
        file = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file:
            self.exe_path.set(file)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, file)

    def _launch_game(self):
        path = self.exe_path.get()
        if os.path.isfile(path):
            subprocess.Popen(path)

    def _apply_resize(self):
        selected = self.tree.focus()
        val = self.single_resize_combo.get()
        if selected and "x" in val:
            w, h = map(int, val.split("x"))
            self._resize_window(int(selected), w, h)

    def _apply_close(self):
        selected = self.tree.focus()
        if selected:
            self._close_window(int(selected))

    def _close_all_windows(self):
        for hwnd in self._get_doomsday_windows():
            self._close_window(hwnd)

    def _resize_all(self):
        val = self.resize_all_combo.get()
        if "x" in val:
            w, h = map(int, val.split("x"))
            for hwnd in self._get_doomsday_windows():
                self._resize_window(hwnd, w, h)

    def _start_autoclicker(self):
        if self.autoclicker.start():
            self.ruchki_status.config(text="Статус: В РАБОТЕ", foreground="lime")

    def _stop_autoclicker(self):
        self.autoclicker.stop()
        self.ruchki_status.config(text="Статус: Неактивно", foreground="gray")

    def _update_table(self):
        def read_and_update():
            hwnds = self._get_doomsday_windows()
            current_ids = set(self.tree.get_children())

            results = []
            for hwnd in hwnds:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    ram = round(proc.memory_info().rss / 1024 / 1024, 1)
                    results.append((hwnd, f"{ram:.1f}"))
                except:
                    results.append((hwnd, "-"))

            def apply_results():
                updated_hwnds = set()
                for hwnd, ram in results:
                    updated_hwnds.add(str(hwnd))
                    if str(hwnd) in current_ids:
                        self.tree.item(str(hwnd), values=(hwnd, ram))
                    else:
                        if str(hwnd) not in self.tree.get_children():
                            self.tree.insert("", "end", iid=str(hwnd), values=(hwnd, ram))

                for iid in current_ids:
                    if iid not in updated_hwnds:
                        try:
                            self.tree.delete(iid)
                        except tk.TclError:
                            pass

            self.root.after(0, apply_results)

        threading.Thread(target=read_and_update, daemon=True).start()

    def _update_system_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.system_stats_label.config(
            text=f"Загрузка системы: CPU {cpu:.0f}%, RAM {ram:.0f}%"
        )
        self._update_table()
        self.root.after(2000, self._update_system_stats)

    def run(self):
        self._update_system_stats()
        self.root.mainloop()


if __name__ == "__main__":
    app = ProcessManager()
    app.run()