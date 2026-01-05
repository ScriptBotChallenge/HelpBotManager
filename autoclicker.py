import os
import threading
import time
import tkinter as tk
from tkinter import messagebox

import pyautogui
from PIL import Image, ImageGrab


class AutoClicker:
    def __init__(self, search_image="search.png"):
        self.search_image = search_image
        self.terminate = False
        self.is_running = False
        self._thread = None
        self._last_root = None

        self.sleep_found = 0.15
        self.sleep_not_found = 0.05
        self.sleep_error = 0.20

    def set_sleeps(self, found, not_found, error=None):
        self.sleep_found = max(0.0, float(found))
        self.sleep_not_found = max(0.0, float(not_found))
        if error is not None:
            self.sleep_error = max(0.0, float(error))

    def start(self):
        if self.is_running:
            return True

        if not os.path.exists(self.search_image):
            messagebox.showerror("Ошибка", f"Файл {self.search_image} не найден!")
            return False

        self.terminate = False
        self.is_running = True
        self._thread = threading.Thread(target=self._clicker_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self.terminate = True
        self.is_running = False
        messagebox.showinfo("Остановлено", "Автокликер остановлен.")

    def _clicker_loop(self):
        pyautogui.PAUSE = 0

        try:
            needle = Image.open(self.search_image)
        except Exception:
            needle = self.search_image

        while not self.terminate:
            try:
                location = pyautogui.locateCenterOnScreen(
                    needle,
                    confidence=0.8,
                    grayscale=True,
                )
                if location:
                    pyautogui.click(location)
                    time.sleep(self.sleep_found)
                else:
                    time.sleep(self.sleep_not_found)
            except Exception:
                time.sleep(self.sleep_error)

        self.is_running = False

    def select_area(self, master=None):
        if self.is_running:
            messagebox.showwarning("Недоступно", "Нельзя выбирать область во время работы кликера.")
            return

        self._last_root = master
        if master:
            master.withdraw()

        def on_cancel():
            if self._last_root:
                self._last_root.deiconify()

        selector = ScreenSelector(
            master=master,
            callback=self._save_area,
            on_cancel=on_cancel,
        )
        selector.window.grab_set()
        selector.window.focus_set()

    def _save_area(self, x1, y1, x2, y2):
        if x1 == x2 or y1 == y2:
            messagebox.showerror("Ошибка", "Область не может быть нулевого размера!")
            if self._last_root:
                self._last_root.deiconify()
            return

        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(self.search_image)
            messagebox.showinfo("Успех", f"Изображение сохранено как {self.search_image}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {e}")
        finally:
            if self._last_root:
                self._last_root.deiconify()


class ScreenSelector:
    def __init__(self, master, callback, on_cancel=None):
        self.callback = callback
        self.on_cancel = on_cancel

        self.window = tk.Toplevel(master) if master else tk.Tk()
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-alpha", 0.3)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="black")

        self.canvas = tk.Canvas(self.window, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.window.bind("<Escape>", self._on_escape)
        self.canvas.focus_set()

    def _on_click(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, outline="red", width=2
        )

    def _on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return

        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        self.window.destroy()
        self.callback(x1, y1, x2, y2)

    def _on_escape(self, _event=None):
        self.window.destroy()
        if self.on_cancel:
            self.on_cancel()