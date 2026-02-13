import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import ttkbootstrap as tb
from ttkbootstrap import Style

from PIL import Image, ImageTk
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt

import json
import os
import datetime

# Helpers OpenCV features
def orb_similarity(img1, img2):
    """Retorna similaridade com ORB (OpenCV) em %"""
    orb = cv2.ORB_create()

    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    if len(matches) == 0:
        return 0.0

    good_matches = [m for m in matches if m.distance < 60]
    return (len(good_matches) / len(matches)) * 100.0

# ZoomableImage
class ZoomableImage:
    def __init__(self, parent, width=360, height=360, bg="#1f1f1f"):
        self.parent = parent
        self.width = width
        self.height = height

        self.canvas = tk.Canvas(parent, width=width, height=height, bg=bg, highlightthickness=0)

        self.pil_image = None
        self.display_image = None
        self.image_id = None

        self.scale = 1.0
        self.min_scale = 0.2
        self.max_scale = 8.0

        self._drag_data = {"x": 0, "y": 0}

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)

    def load_pil(self, pil_image):
        self.pil_image = pil_image.copy()
        self.scale = 1.0
        self._render(center=True)

    def _render(self, center=False):
        if self.pil_image is None:
            self.canvas.delete("all")
            return

        iw, ih = self.pil_image.size
        base_scale = min(self.width / iw, self.height / ih)
        total_scale = base_scale * self.scale
        new_w = max(1, int(iw * total_scale))
        new_h = max(1, int(ih * total_scale))

        resized = self.pil_image.resize((new_w, new_h), Image.LANCZOS)
        self.display_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(self.width//2, self.height//2, image=self.display_image, anchor="center")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        if center:
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)

    def _on_mousewheel(self, event):
        factor = 1.1 if (event.delta > 0 or event.num == 4) else 1/1.1
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        self.scale = new_scale
        self._render()

    def _on_button_press(self, event):
        self.canvas.config(cursor="fleur")
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_move_press(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        try:
            self.canvas.move(self.image_id, dx, dy)
        except:
            pass

    def _on_button_release(self, event):
        self.canvas.config(cursor="arrow")

# Aplicação principal
class ArqueSimilarity:
    SAVE_FILE = "historico.json"

    def __init__(self, root):
        self.root = root
        self.root.title("ArqueSimilarity – OpenCV Edition")
        self.root.geometry("1100x800")
        Style(theme="darkly")

        self.image1 = None
        self.image2 = None
        self.history = []

        self.load_history()

        self.container = ttk.Frame(self.root)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.build_top_area()
        self.build_bottom_area()

        for item in self.history:
            self.history_box.insert(tk.END, item)

    def build_top_area(self):
        top = ttk.Frame(self.container)
        top.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)
        top.grid_rowconfigure(0, weight=1)

        left = ttk.Frame(top)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        left.grid_rowconfigure(1, weight=1)

        ttk.Label(left, text="Imagem 1", font=("Arial",12,"bold")).grid(row=0, column=0, pady=4)
        self.viewer1 = ZoomableImage(left, width=480, height=480)
        self.viewer1.canvas.grid(row=1, column=0, sticky="nsew")
        ttk.Button(left, text="Carregar Imagem 1", bootstyle="info", command=self.load_img1).grid(row=2, column=0, pady=8)

        right = ttk.Frame(top)
        right.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        right.grid_rowconfigure(1, weight=1)

        ttk.Label(right, text="Imagem 2", font=("Arial",12,"bold")).grid(row=0, column=0, pady=4)
        self.viewer2 = ZoomableImage(right, width=480, height=480)
        self.viewer2.canvas.grid(row=1, column=0, sticky="nsew")
        ttk.Button(right, text="Carregar Imagem 2", bootstyle="info", command=self.load_img2).grid(row=2, column=0, pady=8)

    def build_bottom_area(self):
        bottom = ttk.Frame(self.container)
        bottom.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,12))

        controls = ttk.Frame(bottom)
        controls.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            controls.grid_columnconfigure(i, weight=1)

        ttk.Button(controls, text="Comparar Imagens", bootstyle="success", command=self.compare).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(controls, text="Limpar", bootstyle="warning", command=self.clear_all).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(controls, text="Exportar Histórico", bootstyle="info", command=self.export_history).grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        ttk.Button(controls, text="Sair", bootstyle="danger", command=self.root.quit).grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        result_hist = ttk.Frame(bottom)
        result_hist.grid(row=1, column=0, sticky="ew", pady=(6,0))

        result_hist.grid_columnconfigure(0, weight=1)
        result_hist.grid_columnconfigure(1, weight=2)

        # Resultados
        result_frame = ttk.Frame(result_hist)
        result_frame.grid(row=0, column=0, sticky="nsew", padx=(0,6))

        ttk.Label(result_frame, text="Resultado:", font=("Arial",11,"bold")).grid(row=0, column=0, sticky="w")
        self.result_text = tk.Text(result_frame, height=6, width=40, bg="#111", fg="white")
        self.result_text.grid(row=1, column=0, sticky="nsew", pady=4)
        self.result_text.configure(state="disabled")

        # Histórico
        history_frame = ttk.Frame(result_hist)
        history_frame.grid(row=0, column=1, sticky="nsew")

        ttk.Label(history_frame, text="Histórico:", font=("Arial",11,"bold")).grid(row=0, column=0, sticky="w")
        self.history_box = tk.Listbox(history_frame, height=8, bg="#222", fg="white")
        self.history_box.grid(row=1, column=0, sticky="nsew", pady=4)

    #carregando imagens 
    def load_img1(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens","*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")])
        if not path: return
        img = Image.open(path).convert("RGB")
        self.image1 = img
        self.viewer1.load_pil(img)

    def load_img2(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens","*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")])
        if not path: return
        img = Image.open(path).convert("RGB")
        self.image2 = img
        self.viewer2.load_pil(img)
    
    #limpar
    def clear_all(self):
        self.image1 = None
        self.image2 = None
        self.viewer1.canvas.delete("all")
        self.viewer2.canvas.delete("all")
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.configure(state="disabled")

    #comparação 
    def compare(self):
        if self.image1 is None or self.image2 is None:
            messagebox.showerror("Erro", "Carregue as duas imagens.")
            return

        target_size = (300, 300)

        img1_gray = np.array(self.image1.convert("L").resize(target_size))
        img2_gray = np.array(self.image2.convert("L").resize(target_size))

        # SSIM
        try:
            ssim_score = ssim(img1_gray, img2_gray) * 100
        except:
            ssim_score = 0.0

        # ORB
        img1_cv = cv2.cvtColor(np.array(self.image1.resize(target_size)), cv2.COLOR_RGB2BGR)
        img2_cv = cv2.cvtColor(np.array(self.image2.resize(target_size)), cv2.COLOR_RGB2BGR)

        try:
            orb_score = orb_similarity(img1_cv, img2_cv)
        except:
            orb_score = 0.0

        # Similaridade geral
        general_similarity = (ssim_score + orb_score) / 2

        # Texto final
        result_msg = (
            f"SSIM: {ssim_score:.2f}%\n"
            f"ORB: {orb_score:.2f}%\n\n"
            f"A similaridade geral é de {general_similarity:.2f}%"
        )

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, result_msg)
        self.result_text.configure(state="disabled")

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        entry = (
            f"[{now}] SSIM={ssim_score:.2f}% | ORB={orb_score:.2f}% | "
            f"Similaridade={general_similarity:.2f}%"
        )

        self.history.append(entry)
        self.history_box.insert(tk.END, entry)
        self.save_history()

        self.show_graph(ssim_score, orb_score, general_similarity)

    def show_graph(self, ssim_val, orb_val, general_val):
        labels = ["SSIM", "ORB", "Geral"]
        values = [ssim_val, orb_val, general_val]

        plt.figure(figsize=(6,4))
        bars = plt.bar(labels, values)
        plt.ylim(0, 100)
        plt.title("Similaridade")
        plt.ylabel("Percentual (%)")

        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, val + 1.5, f"{val:.1f}%", ha="center")

        plt.tight_layout()
        plt.show()

    #histórico 
    def save_history(self):
        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_history(self):
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []

    def export_history(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("OK", "Histórico exportado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

# Roda o bagulhete
if __name__ == "__main__":
    root = tk.Tk()
    ArqueSimilarity(root)
    root.mainloop()
