import io
import json
import os
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from tkinter import Canvas, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import pyttsx3
import requests

API_ENDPOINT = "http://127.0.0.1:8080/analyze"

BG_DARK = "#05070E"
BG_PANEL = "#0B0F19"
BG_CARD = "#121826"
BG_CARD_HOVER = "#1A2337"
ACCENT_CYAN = "#00F0FF"
ACCENT_NEON_BLUE = "#3B82F6"
ACCENT_EMERALD = "#10B981"
TEXT_MAIN = "#F1F5F9"
TEXT_DIM = "#64748B"
BORDER_SUBTLE = "#1E293B"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


def get_universal_actions(label: str, category: str, search_query: str):
    q_encoded = urllib.parse.quote_plus(search_query)
    cat_upper = category.upper()

    if cat_upper == "AUTOMOTIVE":
        is_two_wheeler = any(
            w in search_query.lower()
            for w in ["motorcycle", "bike", "enfield", "bullet", "scooter", "activa"]
        )
        portal_name = "Bikewale" if is_two_wheeler else "Carwale"
        portal_url = (
            f"https://www.bikewale.com/search/?q={q_encoded}"
            if is_two_wheeler
            else f"https://www.carwale.com/search/?q={q_encoded}"
        )

        return {
            "category": "AUTOMOTIVE",
            "actions": [
                {
                    "name": portal_name,
                    "color": "#E11D48",
                    "text_color": "#FFFFFF",
                    "url": portal_url,
                },
                {
                    "name": "Google Lens",
                    "color": "#3B82F6",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/search?q={q_encoded}+specifications",
                },
                {
                    "name": "Spares",
                    "color": "#F59E0B",
                    "text_color": "#000000",
                    "url": f"https://www.amazon.in/s?k={q_encoded}+accessories",
                },
            ],
        }

    if cat_upper == "LOCATION":
        return {
            "category": "LOCATION / HERITAGE",
            "actions": [
                {
                    "name": "Google Maps",
                    "color": "#10B981",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/maps/search/{q_encoded}",
                },
                {
                    "name": "Wikipedia",
                    "color": "#6366F1",
                    "text_color": "#FFFFFF",
                    "url": f"https://en.wikipedia.org/wiki/Special:Search?search={q_encoded}",
                },
                {
                    "name": "Lens Match",
                    "color": "#3B82F6",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/search?q={q_encoded}",
                },
            ],
        }

    if cat_upper == "FASHION":
        return {
            "category": "FASHION / ATTIRE",
            "actions": [
                {
                    "name": "Amazon",
                    "color": "#FF9900",
                    "text_color": "#000000",
                    "url": f"https://www.amazon.in/s?k={q_encoded}",
                },
                {
                    "name": "Meesho",
                    "color": "#E91E63",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.meesho.com/search?q={q_encoded}",
                },
                {
                    "name": "Visual Match",
                    "color": "#3B82F6",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/search?q={q_encoded}+buy+online",
                },
            ],
        }

    if cat_upper == "FOOD":
        return {
            "category": "CUISINE / FOOD",
            "actions": [
                {
                    "name": "Blinkit",
                    "color": "#10B981",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/search?q=buy+{q_encoded}+online+blinkit",
                },
                {
                    "name": "Recipe",
                    "color": "#06B6D4",
                    "text_color": "#FFFFFF",
                    "url": f"https://www.google.com/search?q={q_encoded}+recipe",
                },
            ],
        }

    return {
        "category": "PRODUCT / ARTIFACT",
        "actions": [
            {
                "name": "Amazon",
                "color": "#FF9900",
                "text_color": "#000000",
                "url": f"https://www.amazon.in/s?k={q_encoded}",
            },
            {
                "name": "Google Lens",
                "color": "#3B82F6",
                "text_color": "#FFFFFF",
                "url": f"https://www.google.com/search?q={q_encoded}",
            },
        ],
    }


class VisionSenseFuturisticStudio(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("VisionSense AI — Autonomous Visual Intelligence Studio")
        self.geometry("1400x880")
        self.minsize(1180, 760)
        self.configure(fg_color=BG_DARK)

        try:
            self.tts = pyttsx3.init()
            self.tts.setProperty("rate", 165)
        except Exception:
            self.tts = None

        self.current_image_path = None
        self.original_image = None
        self.annotated_image = None
        self.current_results = None

        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.tk_image = None

        self._build_studio_layout()

    def _build_studio_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Header HUD
        header = ctk.CTkFrame(self, height=64, fg_color=BG_PANEL, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", padx=(20, 16))

        ctk.CTkLabel(
            brand,
            text="◈",
            font=("Segoe UI", 22, "bold"),
            text_color=ACCENT_CYAN,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            brand,
            text="VisionSense",
            font=("Segoe UI", 16, "bold"),
            text_color=TEXT_MAIN,
        ).pack(side="left")
        ctk.CTkLabel(
            brand,
            text="AUTONOMOUS",
            font=("Segoe UI", 9, "bold"),
            text_color=ACCENT_CYAN,
            fg_color="#082F49",
            corner_radius=4,
            padx=6,
            pady=2,
        ).pack(side="left", padx=(6, 0))

        center_tools = ctk.CTkFrame(header, fg_color="transparent")
        center_tools.pack(side="left", expand=True)

        self.upload_btn = ctk.CTkButton(
            center_tools,
            text="＋ Feed Optical Sensor",
            command=self.select_image,
            font=("Segoe UI", 12, "bold"),
            fg_color=ACCENT_NEON_BLUE,
            hover_color="#2563EB",
            height=34,
            corner_radius=8,
        )
        self.upload_btn.pack(side="left", padx=12)

        zoom_pill = ctk.CTkFrame(center_tools, fg_color=BG_CARD, corner_radius=8)
        zoom_pill.pack(side="left", padx=6)

        ctk.CTkButton(
            zoom_pill,
            text="−",
            width=30,
            height=32,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            command=lambda: self._apply_zoom(0.85),
            font=("Segoe UI", 14),
        ).pack(side="left")
        self.zoom_readout = ctk.CTkLabel(
            zoom_pill,
            text="100%",
            width=46,
            font=("Segoe UI", 11),
            text_color=TEXT_DIM,
        )
        self.zoom_readout.pack(side="left")
        ctk.CTkButton(
            zoom_pill,
            text="+",
            width=30,
            height=32,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            command=lambda: self._apply_zoom(1.15),
            font=("Segoe UI", 14),
        ).pack(side="left")
        ctk.CTkButton(
            zoom_pill,
            text="Fit",
            width=36,
            height=32,
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            command=self._fit_to_screen,
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 2))

        right_tools = ctk.CTkFrame(header, fg_color="transparent")
        right_tools.pack(side="right", padx=(0, 20))

        self.status_badge = ctk.CTkLabel(
            right_tools,
            text="PORT 8080 LISTENING",
            font=("Segoe UI", 9, "bold"),
            text_color=ACCENT_EMERALD,
            fg_color="#064E3B",
            corner_radius=6,
            padx=10,
            pady=4,
        )
        self.status_badge.pack(side="left")

        # Workspace
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # Canvas Area
        self.canvas_card = ctk.CTkFrame(
            body,
            fg_color=BG_PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )
        self.canvas_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.canvas_card.grid_rowconfigure(0, weight=1)
        self.canvas_card.grid_columnconfigure(0, weight=1)

        self.canvas = Canvas(
            self.canvas_card, bg=BG_DARK, highlightthickness=0, cursor="fleur"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._do_pan)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", lambda e: self._on_viewport_resize())

        self.empty_label = ctk.CTkLabel(
            self.canvas_card,
            text="[ OPTICAL SENSOR DISENGAGED ]\nUpload media to initiate open-world visual decomposition.\n\nPan: Left Click + Drag  |  Zoom: Mouse Scroll",
            text_color=TEXT_DIM,
            font=("Consolas", 12),
        )
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # Inspector HUD
        inspector = ctk.CTkFrame(
            body,
            fg_color=BG_PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )
        inspector.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        inspector.grid_rowconfigure(3, weight=1)
        inspector.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inspector,
            text="SYNAPSE NARRATION",
            font=("Segoe UI", 10, "bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")
        self.summary_box = ctk.CTkTextbox(
            inspector,
            height=85,
            wrap="word",
            fg_color=BG_CARD,
            text_color=TEXT_MAIN,
            font=("Segoe UI", 11),
            corner_radius=8,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )
        self.summary_box.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        self.summary_box.insert("1.0", "Sensor idle...")
        self.summary_box.configure(state="disabled")

        actions_bar = ctk.CTkFrame(inspector, fg_color="transparent")
        actions_bar.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        actions_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.speak_btn = ctk.CTkButton(
            actions_bar,
            text="🔊 Vocalize",
            command=self.speak_summary,
            state="disabled",
            height=30,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            text_color=ACCENT_CYAN,
            corner_radius=6,
            font=("Segoe UI", 11, "bold"),
        )
        self.speak_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.json_btn = ctk.CTkButton(
            actions_bar,
            text="Export Telemetry",
            command=self.export_json,
            state="disabled",
            height=30,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            corner_radius=6,
            font=("Segoe UI", 11),
        )
        self.json_btn.grid(row=0, column=1, padx=4, sticky="ew")

        self.save_btn = ctk.CTkButton(
            actions_bar,
            text="Capture Scan",
            command=self.export_image,
            state="disabled",
            height=30,
            fg_color=ACCENT_NEON_BLUE,
            hover_color="#2563EB",
            corner_radius=6,
            font=("Segoe UI", 11, "bold"),
        )
        self.save_btn.grid(row=0, column=2, padx=(4, 0), sticky="ew")

        ctk.CTkLabel(
            inspector,
            text="DECONSTRUCTED ENTITIES & TELEMETRY",
            font=("Segoe UI", 10, "bold"),
            text_color=TEXT_DIM,
        ).grid(row=3, column=0, padx=16, pady=(12, 4), sticky="nw")
        self.feed_scroll = ctk.CTkScrollableFrame(
            inspector,
            fg_color=BG_DARK,
            corner_radius=10,
            border_width=1,
            border_color=BORDER_SUBTLE,
        )
        self.feed_scroll.grid(row=3, column=0, padx=16, pady=(34, 16), sticky="nsew")

    # ----------------- PAN & ZOOM -----------------
    def _start_pan(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _do_pan(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.pan_x += dx
        self.pan_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self._redraw_canvas()

    def _on_mousewheel(self, event):
        factor = 1.15 if event.delta > 0 else 0.85
        self._apply_zoom(factor)

    def _apply_zoom(self, factor):
        if not self.annotated_image:
            return
        new_scale = self.zoom_scale * factor
        if 0.1 <= new_scale <= 5.0:
            self.zoom_scale = new_scale
            self.zoom_readout.configure(text=f"{int(self.zoom_scale * 100)}%")
            self._redraw_canvas()

    def _fit_to_screen(self):
        if not self.annotated_image:
            return
        cw = max(100, self.canvas.winfo_width())
        ch = max(100, self.canvas.winfo_height())
        iw, ih = self.annotated_image.size
        scale_w = cw / iw
        scale_h = ch / ih
        self.zoom_scale = min(scale_w, scale_h) * 0.94
        self.pan_x = (cw - (iw * self.zoom_scale)) / 2
        self.pan_y = (ch - (ih * self.zoom_scale)) / 2
        self.zoom_readout.configure(text=f"{int(self.zoom_scale * 100)}%")
        self._redraw_canvas()

    def _on_viewport_resize(self):
        if self.annotated_image and self.zoom_scale == 1.0:
            self._fit_to_screen()

    def _redraw_canvas(self):
        if not self.annotated_image:
            return
        iw, ih = self.annotated_image.size
        nw = max(1, int(iw * self.zoom_scale))
        nh = max(1, int(ih * self.zoom_scale))

        resized = self.annotated_image.resize((nw, nh), Image.Resampling.BILINEAR)
        self.tk_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=self.tk_image)

    def select_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if path:
            self.current_image_path = path
            self.empty_label.place_forget()
            self.status_badge.configure(
                text="DECONSTRUCTING",
                text_color="#F59E0B",
                fg_color="#78350F",
            )
            self.upload_btn.configure(state="disabled")
            threading.Thread(target=self._run_remote_pipeline, daemon=True).start()

    def _run_remote_pipeline(self):
        try:
            self.original_image = Image.open(self.current_image_path).convert("RGB")
            iw, ih = self.original_image.size

            with open(self.current_image_path, "rb") as f:
                res = requests.post(API_ENDPOINT, files={"file": f}, timeout=30)

            if res.status_code != 200:
                raise ValueError(f"Server response {res.status_code}: {res.text}")

            data = res.json()
            detections = []
            action_cards = []

            for item in data.get("items", []):
                label = item.get("label", "Unknown Entity")
                cat = item.get("category", "PRODUCT")
                query = item.get("search_query", label)
                palette = item.get("palette", ["#00F0FF", "#3B82F6"])
                insights = item.get("insights", "No telemetry spec recorded.")
                ymin, xmin, ymax, xmax = item.get("box_2d", [0, 0, 1000, 1000])

                coords = [
                    int(xmin * iw / 1000),
                    int(ymin * ih / 1000),
                    int(xmax * iw / 1000),
                    int(ymax * ih / 1000),
                ]

                detections.append({"label": label, "box": coords})
                action_cards.append(
                    {
                        "title": label,
                        "query": query,
                        "palette": palette,
                        "insights": insights,
                        "data": get_universal_actions(label, cat, query),
                    }
                )

            self.current_results = {
                "summary": data.get("summary", "Deconstruction complete."),
                "detections": detections,
                "cards": action_cards,
            }

            self._draw_futuristic_reticles(detections)
            self.after(0, self._render_ui)

        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Cortex Error", str(err)))
            self.after(0, lambda: self.upload_btn.configure(state="normal"))
            self.after(
                0,
                lambda: self.status_badge.configure(
                    text="PORT 8080 DOWN",
                    text_color="#EF4444",
                    fg_color="#7F1D1D",
                ),
            )

    def _draw_futuristic_reticles(self, detections):
        annotated = self.original_image.copy()
        draw = ImageDraw.Draw(annotated)
        w, h = annotated.size
        bracket_len = max(10, int(min(w, h) * 0.03))
        line_w = max(2, int(w / 420))
        font_size = max(13, int(w / 50))

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        for d in detections:
            x1, y1, x2, y2 = d["box"]
            tag = f"◈ {d['label'].upper()}"

            draw.rectangle([x1, y1, x2, y2], outline="#1E293B", width=1)

            draw.line([(x1, y1), (x1 + bracket_len, y1)], fill=ACCENT_CYAN, width=line_w)
            draw.line([(x1, y1), (x1, y1 + bracket_len)], fill=ACCENT_CYAN, width=line_w)

            draw.line([(x2, y1), (x2 - bracket_len, y1)], fill=ACCENT_CYAN, width=line_w)
            draw.line([(x2, y1), (x2, y1 + bracket_len)], fill=ACCENT_CYAN, width=line_w)

            draw.line([(x1, y2), (x1 + bracket_len, y2)], fill=ACCENT_CYAN, width=line_w)
            draw.line([(x1, y2), (x1, y2 - bracket_len)], fill=ACCENT_CYAN, width=line_w)

            draw.line([(x2, y2), (x2 - bracket_len, y2)], fill=ACCENT_CYAN, width=line_w)
            draw.line([(x2, y2), (x2 - bracket_len, y2)], fill=ACCENT_CYAN, width=line_w)

            bbox = draw.textbbox((x1, y1), tag, font=font)
            bw = bbox[2] - bbox[0] + 16
            bh = bbox[3] - bbox[1] + 10
            by = max(0, y1 - bh - 3)

            draw.rectangle([x1, by, x1 + bw, by + bh], fill=BG_CARD)
            draw.rectangle([x1, by, x1 + bw, by + bh], outline=ACCENT_CYAN, width=1)
            draw.text((x1 + 8, by + 5), tag, fill=ACCENT_CYAN, font=font)

        self.annotated_image = annotated

    def _render_ui(self):
        self._fit_to_screen()

        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", self.current_results["summary"])
        self.summary_box.configure(state="disabled")

        self.upload_btn.configure(state="normal")
        self.speak_btn.configure(state="normal")
        self.json_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.status_badge.configure(
            text=f"{len(self.current_results['detections'])} TARGETS LOCKED",
            text_color=ACCENT_EMERALD,
            fg_color="#064E3B",
        )

        for child in self.feed_scroll.winfo_children():
            child.destroy()

        cards = self.current_results.get("cards", [])
        if not cards:
            ctk.CTkLabel(
                self.feed_scroll,
                text="No optical telemetry generated.",
                text_color=TEXT_DIM,
                font=("Segoe UI", 11),
            ).pack(pady=28)
            return

        for c in cards:
            card_frame = ctk.CTkFrame(
                self.feed_scroll,
                fg_color=BG_CARD,
                corner_radius=10,
                border_width=1,
                border_color=BORDER_SUBTLE,
            )
            card_frame.pack(fill="x", padx=4, pady=6)

            top = ctk.CTkFrame(card_frame, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 2))
            ctk.CTkLabel(
                top,
                text=c["title"],
                font=("Segoe UI", 12, "bold"),
                text_color=TEXT_MAIN,
            ).pack(side="left")
            ctk.CTkLabel(
                top,
                text=c["data"]["category"],
                font=("Segoe UI", 9, "bold"),
                text_color=ACCENT_CYAN,
            ).pack(side="right")

            ctk.CTkLabel(
                card_frame,
                text=f"✦ {c['insights']}",
                font=("Segoe UI", 10),
                text_color="#94A3B8",
                wraplength=310,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(2, 6))

            palette_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            palette_frame.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(
                palette_frame,
                text="Spectrum:",
                font=("Segoe UI", 9),
                text_color=TEXT_DIM,
            ).pack(side="left", padx=(0, 4))
            for hex_code in c.get("palette", []):
                ctk.CTkLabel(
                    palette_frame,
                    text="   ",
                    fg_color=hex_code,
                    corner_radius=3,
                    width=14,
                    height=14,
                ).pack(side="left", padx=2)

            btn_row = ctk.CTkFrame(card_frame, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 10))
            for act in c["data"]["actions"]:
                ctk.CTkButton(
                    btn_row,
                    text=act["name"],
                    width=75,
                    height=26,
                    fg_color=act["color"],
                    text_color=act["text_color"],
                    font=("Segoe UI", 11, "bold"),
                    corner_radius=6,
                    command=lambda u=act["url"]: webbrowser.open_new_tab(u),
                ).pack(side="left", padx=(0, 6))

    def speak_summary(self):
        if self.current_results and self.tts:
            threading.Thread(
                target=lambda: (
                    self.tts.say(self.current_results["summary"]),
                    self.tts.runAndWait(),
                ),
                daemon=True,
            ).start()

    def export_json(self):
        if not self.current_results:
            return
        p = filedialog.asksaveasfilename(defaultextension=".json")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.current_results, f, indent=2)
            messagebox.showinfo("Exported", f"Telemetry saved to {p}")

    def export_image(self):
        if self.annotated_image:
            p = filedialog.asksaveasfilename(defaultextension=".png")
            if p:
                self.annotated_image.save(p)
                messagebox.showinfo("Exported", f"Optical scan saved to {p}")


if __name__ == "__main__":
    app = VisionSenseFuturisticStudio()
    app.mainloop()