import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
import pyautogui
import threading
import time
import os


class AutoClicker:
    def __init__(self, search_image="search.png"):
        self.search_image = search_image
        self.terminate = False
        self._last_root = None

    def start(self):
        if not os.path.exists(self.search_image):
            messagebox.showerror("Ошибка", f"Файл {self.search_image} не найден!")
            return False

        self.terminate = False
        thread = threading.Thread(target=self._clicker_loop, daemon=True)
        thread.start()
        return True

    def stop(self):
        self.terminate = True
        messagebox.showinfo("Остановлено", "Автокликер остановлен.")

    def _clicker_loop(self):
        while not self.terminate:
            try:
                location = pyautogui.locateCenterOnScreen(self.search_image, confidence=0.8)
                if location:
                    pyautogui.click(location)
                    time.sleep(0.5)
            except Exception:
                pass
            time.sleep(1)

    def select_area(self, master=None):
        self._last_root = master
        if master:
            master.withdraw()

        selector = ScreenSelector(self._save_area)
        selector.grab_set()
        selector.focus_set()

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
    def __init__(self, callback):
        self.callback = callback
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = self.start_y = None
        self.rect = None

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Escape>", self._on_escape)
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

        self.root.destroy()
        self.callback(x1, y1, x2, y2)

    def _on_escape(self, event):
        self.root.destroy()
        if hasattr(self, '_last_root') and self._last_root:
            self._last_root.deiconify()