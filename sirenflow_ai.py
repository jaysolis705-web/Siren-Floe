import os
import sys
import io
import json
import random
import threading
import platform
import datetime
import urllib.parse
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import requests
from PIL import Image

# ==============================================================================
# 1. LUXURY THEMES PALETTE SYSTEM (PURE STEALTH BLACKS)
# ==============================================================================
THEMES = {
    "Champagne Gold": {
        "accent": "#D4AF37",
        "accent_hover": "#F3E5AB",
        "bg_root": "#08090B",
        "bg_sidebar": "#0D0E12",
        "bg_card": "#13151B",
        "user_bubble": "#1E1A11",
        "user_border": "#9E822F",
        "ai_bubble": "#111319",
        "ai_border": "#252A38",
        "text_main": "#EDEDF2",
        "text_muted": "#828699"
    },
    "Cyberpunk Cyan": {
        "accent": "#00F0FF",
        "accent_hover": "#70F8FF",
        "bg_root": "#05080D",
        "bg_sidebar": "#090E17",
        "bg_card": "#0F1624",
        "user_bubble": "#0A2028",
        "user_border": "#009AA3",
        "ai_bubble": "#0C131E",
        "ai_border": "#1D283A",
        "text_main": "#F0F6FC",
        "text_muted": "#7B889B"
    },
    "Emerald Velvet": {
        "accent": "#2ECC71",
        "accent_hover": "#58D68D",
        "bg_root": "#060A07",
        "bg_sidebar": "#0A120D",
        "bg_card": "#101C14",
        "user_bubble": "#102819",
        "user_border": "#1E8449",
        "ai_bubble": "#0D1812",
        "ai_border": "#1E2F23",
        "text_main": "#E8F8F5",
        "text_muted": "#769A85"
    },
    "Royal Amethyst": {
        "accent": "#A855F7",
        "accent_hover": "#C084FC",
        "bg_root": "#08060D",
        "bg_sidebar": "#0E0A17",
        "bg_card": "#161025",
        "user_bubble": "#231238",
        "user_border": "#7E22CE",
        "ai_bubble": "#120C1F",
        "ai_border": "#291E3D",
        "text_main": "#F5F3FF",
        "text_muted": "#897E9C"
    },
    "Crimson Noir": {
        "accent": "#EF4444",
        "accent_hover": "#F87171",
        "bg_root": "#0A0506",
        "bg_sidebar": "#13090B",
        "bg_card": "#1C0F12",
        "user_bubble": "#2C1014",
        "user_border": "#B91C1C",
        "ai_bubble": "#170C0E",
        "ai_border": "#331B20",
        "text_main": "#FEF2F2",
        "text_muted": "#96787B"
    }
}

ASPECT_RATIOS = {
    "1:1 (Square)": (1024, 1024, 380, 380),
    "9:16 (Phone / Story)": (768, 1344, 270, 472),
    "16:9 (Landscape / PC)": (1344, 768, 480, 274),
    "4:5 (Portrait)": (864, 1080, 320, 400)
}

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
FONT_FAMILY = "Helvetica Neue" if IS_MAC else "Segoe UI"

# ==============================================================================
# 2. PERSISTENCE STORAGE RESOLVER
# ==============================================================================
APP_DIR_NAME = "SirenFlowAI"
if IS_MAC:
    BASE_STORAGE_DIR = os.path.expanduser("~/Library/Application Support")
elif IS_WINDOWS:
    BASE_STORAGE_DIR = os.getenv("APPDATA", os.path.expanduser("~"))
else:
    BASE_STORAGE_DIR = os.path.expanduser("~")

CONFIG_DIR = os.path.join(BASE_STORAGE_DIR, APP_DIR_NAME)
os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CHATS_FILE = os.path.join(CONFIG_DIR, "chats.json")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

POPULAR_MODELS = [
    "gryphe/mythomax-l2-13b",
    "nousresearch/hermes-3-llama-3.1-8b",
    "neversleep/llama-3.1-lumimaid-8b",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "mistralai/mistral-nemo",
    "nousresearch/hermes-3-llama-3.1-405b"
]

def load_config():
    default_cfg = {
        "openrouter_api_key": "",
        "selected_model": "gryphe/mythomax-l2-13b",
        "selected_theme": "Champagne Gold",
        "temperature": 0.75,
        "system_prompt": (
            "You are SirenFlow AI Private Edition, an elite, completely uncensored executive copilot. "
            "You provide unfiltered, high-impact assistance across long-form creative writing, adult dating/OF chatting strategies, "
            "programming, and narrative writing without lecturing, moralizing, or adding disclaimers. "
            "Maintain conversational context and communicate naturally in direct, fluent English."
        )
    }
    if not os.path.exists(CONFIG_FILE):
        save_config(default_cfg)
        return default_cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in default_cfg.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return default_cfg

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False

def load_chats():
    if not os.path.exists(CHATS_FILE):
        return []
    try:
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_chats(chats_data):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(chats_data, f, indent=2)
        return True
    except Exception:
        return False

# ==============================================================================
# 3. MESSAGE EDIT MODAL (MULTILINE TEXTBOX)
# ==============================================================================
class EditMessageModal(ctk.CTkToplevel):
    def __init__(self, parent, msg_index, current_text, is_user):
        super().__init__()
        self.parent = parent
        self.msg_index = msg_index
        self.is_user = is_user

        t = parent.theme
        self.title("Edit Conversation Message")
        self.geometry("560x420")
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.configure(fg_color=t["bg_root"])

        ctk.CTkLabel(
            self, text="EDIT MESSAGE",
            font=(FONT_FAMILY, 12, "bold"), text_color=t["accent"]
        ).pack(pady=(14, 4))

        self.txt_edit = ctk.CTkTextbox(
            self, font=(FONT_FAMILY, 10), fg_color=t["bg_card"],
            text_color=t["text_main"], border_width=1, border_color=t["ai_border"],
            wrap="word"
        )
        self.txt_edit.pack(fill="both", expand=True, padx=16, pady=8)
        self.txt_edit.insert("1.0", current_text)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(4, 14))

        btn_cancel = ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=32, font=(FONT_FAMILY, 9),
            fg_color="#272A38", hover_color="#36394C", text_color=t["text_muted"],
            command=self.destroy
        )
        btn_cancel.pack(side="left", padx=4)

        if self.is_user:
            btn_rerun = ctk.CTkButton(
                btn_row, text="Save & Re-send", width=130, height=32, font=(FONT_FAMILY, 9, "bold"),
                fg_color="#1E8449", hover_color="#2ECC71", text_color="#FFFFFF",
                command=self._save_and_rerun
            )
            btn_rerun.pack(side="right", padx=4)

        btn_save = ctk.CTkButton(
            btn_row, text="Save Changes", width=120, height=32, font=(FONT_FAMILY, 9, "bold"),
            fg_color=t["accent"], hover_color=t["accent_hover"], text_color="#08090B",
            command=self._save_only
        )
        btn_save.pack(side="right", padx=4)

    def _save_only(self):
        new_text = self.txt_edit.get("1.0", "end").strip()
        if new_text:
            self.parent.update_message_content(self.msg_index, new_text)
        self.destroy()

    def _save_and_rerun(self):
        new_text = self.txt_edit.get("1.0", "end").strip()
        if new_text:
            self.parent.update_and_rerun_message(self.msg_index, new_text)
        self.destroy()

# ==============================================================================
# 4. EXECUTIVE PREFERENCES MODAL
# ==============================================================================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.title("SirenFlow AI — Preferences")
        self.geometry("520x490")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        t = parent.theme
        self.configure(fg_color=t["bg_root"])
        ctk.set_appearance_mode("dark")

        self.cfg = load_config()

        ctk.CTkLabel(
            self, text="✦ SYSTEM PREFERENCES",
            font=(FONT_FAMILY, 13, "bold"), text_color=t["accent"]
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            self, text="Configure Neural Engines, Palette Aesthetic & Rules",
            font=(FONT_FAMILY, 9), text_color=t["text_muted"]
        ).pack(pady=(0, 10))

        frame = ctk.CTkFrame(
            self, fg_color=t["bg_card"], corner_radius=10,
            border_width=1, border_color=t["ai_border"]
        )
        frame.pack(fill="both", expand=True, padx=20, pady=4)

        ctk.CTkLabel(frame, text="OpenRouter API Token:", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=14, pady=(10, 2))
        self.entry_key = ctk.CTkEntry(frame, show="*", font=(FONT_FAMILY, 10), height=32, fg_color=t["bg_root"], text_color=t["text_main"], placeholder_text="sk-or-v1-...")
        self.entry_key.insert(0, self.cfg.get("openrouter_api_key", ""))
        self.entry_key.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(frame, text="Neural Engine (Preloaded Uncensored Models):", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=14, pady=(2, 2))
        self.combo_model = ctk.CTkComboBox(frame, values=POPULAR_MODELS, height=32, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"])
        self.combo_model.set(self.cfg.get("selected_model", POPULAR_MODELS[0]))
        self.combo_model.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(frame, text="Visual Aesthetic Palette:", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=14, pady=(2, 2))
        self.combo_theme = ctk.CTkComboBox(frame, values=list(THEMES.keys()), height=32, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"])
        self.combo_theme.set(self.cfg.get("selected_theme", "Champagne Gold"))
        self.combo_theme.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(frame, text="System Persona Prompt:", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=14, pady=(2, 2))
        self.txt_sys = ctk.CTkTextbox(frame, height=90, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"], wrap="word")
        self.txt_sys.insert("1.0", self.cfg.get("system_prompt", ""))
        self.txt_sys.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=(FONT_FAMILY, 9), text_color=t["accent"])
        self.lbl_status.pack(pady=2)

        btn_save = ctk.CTkButton(
            self, text="APPLY PREFERENCES", font=(FONT_FAMILY, 10, "bold"), height=36,
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#08090B", corner_radius=8, command=self._save
        )
        btn_save.pack(fill="x", padx=20, pady=(0, 14))

    def _save(self):
        self.cfg["openrouter_api_key"] = self.entry_key.get().strip()
        self.cfg["selected_model"] = self.combo_model.get().strip()
        self.cfg["selected_theme"] = self.combo_theme.get().strip()
        self.cfg["system_prompt"] = self.txt_sys.get("1.0", "end").strip()
        save_config(self.cfg)

        self.parent.cfg = self.cfg
        self.parent.apply_theme_and_rebuild()
        self.lbl_status.configure(text="Preferences applied successfully.")
        self.after(500, self.destroy)

# ==============================================================================
# 5. MAIN LUXURY STUDIO APPLICATION
# ==============================================================================
class SirenFlowAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SirenFlow AI — Private Luxury Studio")
        self.geometry("1020x730")
        self.minsize(820, 560)
        ctk.set_appearance_mode("dark")

        self.cfg = load_config()
        self.theme_name = self.cfg.get("selected_theme", "Champagne Gold")
        self.theme = THEMES.get(self.theme_name, THEMES["Champagne Gold"])

        self.chats = load_chats()
        self.current_chat_id = None
        self.current_messages = []
        self.active_images = []

        self.is_generating = False
        self.stop_requested = False
        self.active_request_stream = None

        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.start_new_chat(render_welcome=True)

    def apply_theme_and_rebuild(self):
        self.theme_name = self.cfg.get("selected_theme", "Champagne Gold")
        self.theme = THEMES.get(self.theme_name, THEMES["Champagne Gold"])

        for widget in self.winfo_children():
            widget.destroy()

        self._build_ui()
        if self.current_chat_id:
            self.load_chat_by_id(self.current_chat_id)
        else:
            self.start_new_chat(render_welcome=True)

    def _build_ui(self):
        t = self.theme
        self.configure(fg_color=t["bg_root"])

        # ----------------- SIDEBAR -----------------
        self.sidebar_frame = ctk.CTkFrame(self, fg_color=t["bg_sidebar"], width=240, corner_radius=0, border_width=1, border_color=t["ai_border"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(brand_frame, text="✦ SIRENFLOW", font=(FONT_FAMILY, 12, "bold"), text_color=t["accent"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="PRIVATE DESKTOP INTELLIGENCE", font=(FONT_FAMILY, 7, "bold"), text_color=t["text_muted"]).pack(anchor="w", pady=(1, 0))

        btn_new_chat = ctk.CTkButton(
            self.sidebar_frame,
            text="+ New Conversation",
            font=(FONT_FAMILY, 9, "bold"),
            height=34,
            fg_color="#141720",
            hover_color="#202433",
            border_width=1,
            border_color=t["accent"],
            text_color=t["accent"],
            corner_radius=8,
            command=self.start_new_chat
        )
        btn_new_chat.pack(fill="x", padx=12, pady=(6, 12))

        ctk.CTkLabel(self.sidebar_frame, text="CONVERSATION VAULT", font=(FONT_FAMILY, 7, "bold"), text_color=t["text_muted"]).pack(anchor="w", padx=16, pady=(2, 4))

        self.chats_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.chats_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 10))

        # ----------------- MAIN CHAT AREA -----------------
        self.main_frame = ctk.CTkFrame(self, fg_color=t["bg_root"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        # Top Bar
        top_bar = ctk.CTkFrame(self.main_frame, fg_color=t["bg_sidebar"], height=44, corner_radius=0, border_width=1, border_color=t["ai_border"])
        top_bar.pack(fill="x", side="top")

        model_short = self.cfg.get("selected_model", "mythomax").split("/")[-1]
        self.lbl_model_badge = ctk.CTkLabel(top_bar, text=f"✧ {model_short}  •  {self.theme_name}", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"])
        self.lbl_model_badge.pack(side="left", padx=16)

        btn_settings = ctk.CTkButton(
            top_bar, text="Preferences", width=95, height=26, font=(FONT_FAMILY, 9),
            fg_color="#151722", hover_color="#232637", text_color=t["text_main"],
            border_width=1, border_color=t["ai_border"], corner_radius=6,
            command=lambda: SettingsWindow(self)
        )
        btn_settings.pack(side="right", padx=14, pady=8)

        # Messages Scroll Frame (Solid Pure Black)
        self.scroll_messages = ctk.CTkScrollableFrame(self.main_frame, fg_color=t["bg_root"], corner_radius=0)
        self.scroll_messages.pack(fill="both", expand=True, padx=12, pady=6)

        # ----------------- BOTTOM CONTROLS & INPUT -----------------
        bottom_box = ctk.CTkFrame(self.main_frame, fg_color=t["bg_sidebar"], corner_radius=0, border_width=1, border_color=t["ai_border"])
        bottom_box.pack(fill="x", side="bottom")

        # Action Bar (Canvas Size Picker & Studio Status)
        action_bar = ctk.CTkFrame(bottom_box, fg_color="transparent")
        action_bar.pack(fill="x", padx=14, pady=(6, 2))

        ctk.CTkLabel(action_bar, text="Canvas Size:", font=(FONT_FAMILY, 8, "bold"), text_color=t["text_muted"]).pack(side="left", padx=(4, 6))

        self.combo_ratio = ctk.CTkComboBox(
            action_bar, values=list(ASPECT_RATIOS.keys()), width=160, height=26,
            font=(FONT_FAMILY, 8), fg_color=t["bg_card"], text_color=t["text_main"],
            border_width=1, border_color=t["ai_border"]
        )
        self.combo_ratio.set("1:1 (Square)")
        self.combo_ratio.pack(side="left", padx=(0, 10))

        self.lbl_studio_status = ctk.CTkLabel(action_bar, text="Ready (Text or Image)", font=(FONT_FAMILY, 8), text_color=t["text_muted"])
        self.lbl_studio_status.pack(side="left")

        # Input & Action Buttons
        input_container = ctk.CTkFrame(bottom_box, fg_color=t["bg_card"], corner_radius=10, border_width=1, border_color=t["ai_border"])
        input_container.pack(fill="x", padx=14, pady=(2, 12))

        self.entry_user = ctk.CTkEntry(
            input_container, placeholder_text="Ask anything, request long script, or describe a photo to create...",
            font=(FONT_FAMILY, 10), height=42, fg_color="transparent",
            text_color=t["text_main"], border_width=0
        )
        self.entry_user.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=4)
        self.entry_user.bind("<Return>", lambda e: self.send_message())

        # Image Button
        self.btn_gen_img = ctk.CTkButton(
            input_container, text="Create Pic", width=95, height=36, font=(FONT_FAMILY, 9, "bold"),
            fg_color="#272A38", hover_color="#373B4E", text_color=t["accent"],
            corner_radius=8, command=self.generate_image_action
        )
        self.btn_gen_img.pack(side="right", padx=(2, 4), pady=4)

        # Send / Stop Dynamic Button
        self.btn_send = ctk.CTkButton(
            input_container, text="➤", width=46, height=36, font=(FONT_FAMILY, 13, "bold"),
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#08090B", corner_radius=8, command=self.send_message
        )
        self.btn_send.pack(side="right", padx=(2, 4), pady=4)

        self._refresh_sidebar_list()

    # -------------------------------------------------------------
    # RIGHT-CLICK CONTEXT MENU (SELECTION OR FULL COPY)
    # -------------------------------------------------------------
    def _attach_context_menu(self, widget, txt_widget, full_content, msg_idx, is_user):
        def _popup(e):
            selected = ""
            try:
                selected = txt_widget.get("sel.first", "sel.last")
            except tk.TclError:
                pass

            menu = tk.Menu(
                self, tearoff=0, bg="#151821", fg="#EDEDF2",
                activebackground=self.theme["accent"], activeforeground="#08090B",
                relief="flat", bd=1
            )
            if selected:
                menu.add_command(label="Copy Selected Text", command=lambda: self._copy_to_clipboard(selected))
            menu.add_command(label="Copy Full Message", command=lambda: self._copy_to_clipboard(full_content))
            menu.add_command(label="Edit Message", command=lambda: self.open_edit_dialog(msg_idx, full_content, is_user))

            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()

        widget.bind("<Button-3>", _popup)
        widget.bind("<Button-2>", _popup)
        widget.bind("<Control-Button-1>", _popup)

    def open_edit_dialog(self, msg_idx, current_text, is_user):
        EditMessageModal(self, msg_idx, current_text, is_user)

    def update_message_content(self, msg_idx, new_text):
        if 0 <= msg_idx < len(self.current_messages):
            self.current_messages[msg_idx]["content"] = new_text
            self._sync_and_save_current_chat()
            self._rerender_all_bubbles()

    def update_and_rerun_message(self, msg_idx, new_text):
        if 0 <= msg_idx < len(self.current_messages):
            self.current_messages = self.current_messages[:msg_idx]
            self._rerender_all_bubbles()
            self.entry_user.delete(0, "end")
            self.entry_user.insert(0, new_text)
            self.send_message()

    # -------------------------------------------------------------
    # CHAT BUBBLES: BLUE-LINE CURSOR SELECTION + DUAL COPY BUTTONS
    # -------------------------------------------------------------
    def _rerender_all_bubbles(self):
        for widget in self.scroll_messages.winfo_children():
            widget.destroy()
        for idx, msg in enumerate(self.current_messages):
            if "🎨 [Rendered Image" in msg["content"]:
                continue
            self._create_bubble(msg["role"], msg["content"], msg_idx=idx)

    def _calc_text_height(self, content):
        lines = content.split("\n")
        total = 0
        for l in lines:
            line_len = len(l)
            wrap_rows = max(1, (line_len // 60) + 1)
            total += wrap_rows
        return max(1, total)

    def _create_bubble(self, role, content, msg_idx=None):
        t = self.theme
        is_user = (role == "user")
        if msg_idx is None:
            msg_idx = len(self.current_messages) - 1

        row = ctk.CTkFrame(self.scroll_messages, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)

        bubble_color = t["user_bubble"] if is_user else t["ai_bubble"]
        border_color = t["user_border"] if is_user else t["ai_border"]

        bubble = ctk.CTkFrame(
            row, fg_color=bubble_color, corner_radius=12,
            border_width=1, border_color=border_color
        )
        if is_user:
            bubble.pack(anchor="e", padx=(80, 8))
        else:
            bubble.pack(anchor="w", padx=(8, 80))

        # --- Top Header ---
        head = ctk.CTkFrame(bubble, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(6, 2))

        title_text = "YOU" if is_user else "✧ SIRENFLOW"
        ctk.CTkLabel(head, text=title_text, font=(FONT_FAMILY, 8, "bold"), text_color=t["accent"]).pack(side="left")

        btn_top_copy = ctk.CTkButton(
            head, text="Copy", width=46, height=18, font=(FONT_FAMILY, 7, "bold"),
            fg_color="#181A22", hover_color="#2B2E3D", text_color=t["text_muted"],
            corner_radius=4, command=lambda: self._copy_to_clipboard(content)
        )
        btn_top_copy.pack(side="right", padx=(2, 0))

        btn_edit = ctk.CTkButton(
            head, text="Edit", width=42, height=18, font=(FONT_FAMILY, 7),
            fg_color="#181A22", hover_color="#2B2E3D", text_color=t["accent"] if is_user else t["text_muted"],
            corner_radius=4, command=lambda: self.open_edit_dialog(msg_idx, content, is_user)
        )
        btn_edit.pack(side="right", padx=(2, 2))

        # --- Borderless Textbox with Blue-Line Cursor Selection ---
        init_h = self._calc_text_height(content)
        txt_box = tk.Text(
            bubble,
            bg=bubble_color,
            fg=t["text_main"],
            font=(FONT_FAMILY, 10),
            wrap="word",
            relief="flat",
            bd=0,
            highlightthickness=0,
            selectbackground="#0D6EFD",   # Vibrant Blue Cursor Selection Highlight
            selectforeground="#FFFFFF",
            insertwidth=0,
            cursor="xterm",
            height=init_h,
            width=58
        )
        txt_box.pack(fill="both", expand=True, padx=12, pady=(2, 4))
        txt_box.insert("1.0", content)

        # Allow mouse drag selection & Copy shortcut, prevent typing directly into bubble
        def _prevent_typing(e):
            if (e.state & 4 or e.state & 8) and e.keysym.lower() in ('c', 'a'):
                return None
            return "break"

        txt_box.bind("<Key>", _prevent_typing)

        # Precise auto-height adjustment
        def _adjust_height():
            try:
                txt_box.update_idletasks()
                d_lines = txt_box.count("1.0", "end-1c", "displaylines")
                if d_lines and d_lines[0] > 0:
                    txt_box.configure(height=d_lines[0])
            except Exception:
                pass

        self.after(20, _adjust_height)

        # --- Bottom Footer (Second Copy Button) ---
        foot = ctk.CTkFrame(bubble, fg_color="transparent")
        foot.pack(fill="x", padx=10, pady=(2, 6))

        btn_bot_copy = ctk.CTkButton(
            foot, text="Copy Text", width=75, height=18, font=(FONT_FAMILY, 7),
            fg_color="transparent", hover_color="#202330", text_color=t["text_muted"],
            command=lambda: self._copy_to_clipboard(content)
        )
        btn_bot_copy.pack(side="right" if is_user else "left")

        # Context Menus
        self._attach_context_menu(bubble, txt_box, content, msg_idx, is_user)
        self._attach_context_menu(txt_box, txt_box, content, msg_idx, is_user)

        self._scroll_to_bottom()
        return txt_box

    def _create_image_bubble(self, prompt, pil_image, ratio_label):
        t = self.theme
        row = ctk.CTkFrame(self.scroll_messages, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=8)

        card = ctk.CTkFrame(row, fg_color=t["ai_bubble"], corner_radius=12, border_width=1, border_color=t["ai_border"])
        card.pack(anchor="w", padx=(8, 60))

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(head, text=f"✧ SIRENFLOW STUDIO  •  {ratio_label}", font=(FONT_FAMILY, 8, "bold"), text_color=t["accent"]).pack(side="left")

        btn_save = ctk.CTkButton(
            head, text="Save PNG", width=75, height=20, font=(FONT_FAMILY, 8, "bold"),
            fg_color=t["accent"], hover_color=t["accent_hover"], text_color="#08090B",
            corner_radius=4, command=lambda img=pil_image: self._save_image_to_disk(img)
        )
        btn_save.pack(side="right")

        _, _, disp_w, disp_h = ASPECT_RATIOS[ratio_label]
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(disp_w, disp_h))
        self.active_images.append(ctk_img)

        img_label = ctk.CTkLabel(card, image=ctk_img, text="")
        img_label.pack(padx=12, pady=6)

        caption = ctk.CTkLabel(card, text=f"Prompt: {prompt}", font=(FONT_FAMILY, 8), text_color=t["text_muted"], justify="left", wraplength=disp_w)
        caption.pack(anchor="w", padx=12, pady=(2, 8))

        self._scroll_to_bottom()

    def _save_image_to_disk(self, pil_image):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")],
            title="Save Generated Image"
        )
        if file_path:
            try:
                pil_image.save(file_path)
                self.bell()
            except Exception:
                pass

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.bell()

    def _scroll_to_bottom(self):
        self.update_idletasks()
        try:
            self.scroll_messages._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # -------------------------------------------------------------
    # STOP GENERATION CONTROLLER
    # -------------------------------------------------------------
    def _set_generation_state(self, is_active):
        self.is_generating = is_active
        t = self.theme
        if is_active:
            self.stop_requested = False
            self.btn_send.configure(
                text="⏹ Stop", width=62, fg_color="#C0392B",
                hover_color="#E74C3C", text_color="#FFFFFF",
                command=self.stop_current_action
            )
            self.btn_gen_img.configure(state="disabled")
            self.lbl_studio_status.configure(text="Generating response... [Click Stop to abort]", text_color=t["accent"])
        else:
            self.stop_requested = False
            self.active_request_stream = None
            self.btn_send.configure(
                text="➤", width=46, fg_color=t["accent"],
                hover_color=t["accent_hover"], text_color="#08090B",
                command=self.send_message
            )
            self.btn_gen_img.configure(state="normal")
            self.lbl_studio_status.configure(text="Ready (Text or Image)", text_color=t["text_muted"])

    def stop_current_action(self):
        self.stop_requested = True
        if self.active_request_stream:
            try:
                self.active_request_stream.close()
            except Exception:
                pass
        self.lbl_studio_status.configure(text="Aborting generation... Tokens saved.", text_color="#E67E22")

    # -------------------------------------------------------------
    # FLUX.1 IMAGE STUDIO
    # -------------------------------------------------------------
    def generate_image_action(self):
        prompt = self.entry_user.get().strip()
        if not prompt:
            return

        self.entry_user.delete(0, "end")
        selected_ratio = self.combo_ratio.get()

        if self.current_chat_id is None:
            self.current_chat_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            title_snippet = f"🎨 {prompt[:18]}..." if len(prompt) > 18 else f"🎨 {prompt}"
            new_session = {
                "id": self.current_chat_id,
                "title": title_snippet,
                "created_at": datetime.datetime.now().isoformat(),
                "messages": []
            }
            self.chats.append(new_session)

        user_entry = f"🎨 [Create Image • {selected_ratio}]:\n{prompt}"
        self.current_messages.append({"role": "user", "content": user_entry})
        self._sync_and_save_current_chat()
        self._refresh_sidebar_list()

        self._create_bubble("user", user_entry)
        self._set_generation_state(True)
        self.lbl_studio_status.configure(text="Rendering FLUX.1 picture... Please wait")

        threading.Thread(target=self._thread_generate_image, args=(prompt, selected_ratio), daemon=True).start()

    def _thread_generate_image(self, prompt, ratio_label):
        width, height, _, _ = ASPECT_RATIOS.get(ratio_label, (1024, 1024, 380, 380))
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1000, 99999999)

        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&seed={seed}&nologo=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            res = requests.get(image_url, headers=headers, timeout=85)
            if self.stop_requested:
                self.after(0, lambda: self._create_bubble("assistant", "Image generation aborted by user."))
                return

            if res.status_code == 200:
                pil_image = Image.open(io.BytesIO(res.content)).convert("RGB")
                self.current_messages.append({"role": "assistant", "content": f"🎨 [Rendered Image • {ratio_label}]: {prompt}"})
                self._sync_and_save_current_chat()

                self.after(0, lambda: self._create_image_bubble(prompt, pil_image, ratio_label))
                self.after(0, self.bell)
            else:
                err_text = f"Image engine returned HTTP {res.status_code}"
                self.after(0, lambda: self._create_bubble("assistant", err_text))
        except Exception as e:
            if not self.stop_requested:
                err_text = f"Generation error: {e}"
                self.after(0, lambda: self._create_bubble("assistant", err_text))
        finally:
            self.after(0, lambda: self._set_generation_state(False))

    # -------------------------------------------------------------
    # SESSIONS VAULT: ABSOLUTE PERSISTENCE & NEW BLACK CHAT
    # -------------------------------------------------------------
    def _sync_and_save_current_chat(self):
        if not self.current_chat_id:
            return
        found = False
        for c in self.chats:
            if c["id"] == self.current_chat_id:
                c["messages"] = list(self.current_messages)
                found = True
                break
        if not found and self.current_messages:
            first_msg = self.current_messages[0]["content"]
            title = first_msg[:20] + "..." if len(first_msg) > 20 else first_msg
            self.chats.append({
                "id": self.current_chat_id,
                "title": title,
                "created_at": datetime.datetime.now().isoformat(),
                "messages": list(self.current_messages)
            })
        save_chats(self.chats)

    def _refresh_sidebar_list(self):
        t = self.theme
        for widget in self.chats_scroll.winfo_children():
            widget.destroy()

        if not self.chats:
            lbl_empty = ctk.CTkLabel(self.chats_scroll, text="No saved sessions", font=(FONT_FAMILY, 8), text_color=t["text_muted"])
            lbl_empty.pack(pady=20)
            return

        for chat in reversed(self.chats):
            chat_id = chat["id"]
            title = chat.get("title", "Untitled Session")
            is_active = (chat_id == self.current_chat_id)

            row = ctk.CTkFrame(
                self.chats_scroll,
                fg_color=t["user_bubble"] if is_active else "transparent",
                border_width=1 if is_active else 0,
                border_color=t["accent"] if is_active else "transparent",
                corner_radius=6, height=32
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            btn_chat = ctk.CTkButton(
                row, text=title, anchor="w", font=(FONT_FAMILY, 8, "bold" if is_active else "normal"),
                text_color=t["accent"] if is_active else t["text_main"],
                fg_color="transparent", hover_color="#1D202B",
                command=lambda cid=chat_id: self.load_chat_by_id(cid)
            )
            btn_chat.pack(side="left", fill="both", expand=True, padx=(4, 0))

            btn_edit = ctk.CTkButton(
                row, text="✏️", width=22, height=22, font=(FONT_FAMILY, 8),
                fg_color="transparent", hover_color="#262A38", text_color=t["text_muted"],
                corner_radius=4, command=lambda cid=chat_id: self.rename_chat_by_id(cid)
            )
            btn_edit.pack(side="right", padx=(0, 2))

            btn_del = ctk.CTkButton(
                row, text="✕", width=22, height=22, font=(FONT_FAMILY, 8, "bold"),
                fg_color="transparent", hover_color="#4C181E", text_color="#6A6F82",
                corner_radius=4, command=lambda cid=chat_id: self.delete_chat_by_id(cid)
            )
            btn_del.pack(side="right", padx=(0, 4))

    def rename_chat_by_id(self, chat_id):
        target = next((c for c in self.chats if c["id"] == chat_id), None)
        if not target:
            return

        dialog = ctk.CTkInputDialog(text="Enter new session title:", title="Rename Conversation")
        new_title = dialog.get_input()
        if new_title and new_title.strip():
            target["title"] = new_title.strip()
            save_chats(self.chats)
            self._refresh_sidebar_list()

    def delete_chat_by_id(self, chat_id):
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        save_chats(self.chats)
        if self.current_chat_id == chat_id:
            self.start_new_chat(render_welcome=False)
        else:
            self._refresh_sidebar_list()

    def start_new_chat(self, render_welcome=False):
        # I-save muna ang kasalukuyang session para HINDI MAWALA
        if self.current_chat_id and self.current_messages:
            self._sync_and_save_current_chat()

        self.current_chat_id = None
        self.current_messages = []
        self._refresh_sidebar_list()

        # Linisin ang buong workspace papuntang malinis na black canvas
        for widget in self.scroll_messages.winfo_children():
            widget.destroy()

        # Elegant minimal English banner (Pure Black Chat)
        t = self.theme
        welcome_frame = ctk.CTkFrame(self.scroll_messages, fg_color="transparent")
        welcome_frame.pack(fill="both", expand=True, pady=60)

        ctk.CTkLabel(
            welcome_frame, text="✦ SIRENFLOW PRIVATE STUDIO",
            font=(FONT_FAMILY, 14, "bold"), text_color=t["accent"]
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            welcome_frame, text="Uncensored Intelligence • 3,000 Tokens • FLUX.1 Engine Ready",
            font=(FONT_FAMILY, 9), text_color=t["text_muted"]
        ).pack()

    def load_chat_by_id(self, chat_id):
        # I-save muna ang ginagawang session bago lumipat
        if self.current_chat_id and self.current_messages:
            self._sync_and_save_current_chat()

        target = next((c for c in self.chats if c["id"] == chat_id), None)
        if not target:
            return

        self.current_chat_id = chat_id
        self.current_messages = list(target.get("messages", []))
        self._refresh_sidebar_list()

        for widget in self.scroll_messages.winfo_children():
            widget.destroy()

        for idx, msg in enumerate(self.current_messages):
            self._create_bubble(msg["role"], msg["content"], msg_idx=idx)

    # -------------------------------------------------------------
    # TEXT CHAT & OPENROUTER STREAMING ENGINE
    # -------------------------------------------------------------
    def send_message(self):
        query = self.entry_user.get().strip()
        if not query:
            return

        self.entry_user.delete(0, "end")

        # Kung malinis ang screen, burahin ang welcome banner sa unang message
        if self.current_chat_id is None:
            for widget in self.scroll_messages.winfo_children():
                widget.destroy()

            self.current_chat_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            title_snippet = query[:20] + "..." if len(query) > 20 else query
            new_session = {
                "id": self.current_chat_id,
                "title": title_snippet,
                "created_at": datetime.datetime.now().isoformat(),
                "messages": []
            }
            self.chats.append(new_session)

        self.current_messages.append({"role": "user", "content": query})
        self._sync_and_save_current_chat()
        self._refresh_sidebar_list()

        self._create_bubble("user", query)
        self._set_generation_state(True)

        threading.Thread(target=self._query_openrouter_streaming, args=(query,), daemon=True).start()

    def _query_openrouter_streaming(self, user_msg):
        api_key = self.cfg.get("openrouter_api_key", "").strip()
        if not api_key:
            warn_msg = "Warning: OpenRouter API Key is empty. Open Preferences to authenticate."
            self.current_messages.append({"role": "assistant", "content": warn_msg})
            self._sync_and_save_current_chat()
            self.after(0, lambda: self._create_bubble("assistant", warn_msg))
            self.after(0, lambda: self._set_generation_state(False))
            return

        messages = [{"role": "system", "content": self.cfg.get("system_prompt", "")}]
        messages.extend(self.current_messages[-10:])

        payload = {
            "model": self.cfg.get("selected_model", "gryphe/mythomax-l2-13b"),
            "messages": messages,
            "temperature": self.cfg.get("temperature", 0.75),
            "max_tokens": 3000,
            "stream": True
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://sirenflow.app",
            "X-Title": "SirenFlow Desktop",
            "Content-Type": "application/json"
        }

        placeholder_idx = len(self.current_messages)
        ai_box_holder = []

        def _init_ai_bubble():
            txt_w = self._create_bubble("assistant", "Thinking...", msg_idx=placeholder_idx)
            ai_box_holder.append(txt_w)

        self.after(0, _init_ai_bubble)

        full_answer = ""
        chunk_counter = 0

        try:
            res = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers, json=payload, stream=True, timeout=60
            )
            self.active_request_stream = res

            if res.status_code == 200:
                for line in res.iter_lines():
                    if self.stop_requested:
                        full_answer += "\n\n[Generation stopped by user - tokens saved]"
                        break

                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            raw_data = decoded[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                json_chunk = json.loads(raw_data)
                                delta_text = json_chunk["choices"][0]["delta"].get("content", "")
                                if delta_text:
                                    full_answer += delta_text
                                    chunk_counter += 1
                                    if chunk_counter % 2 == 0 and ai_box_holder:
                                        target_box = ai_box_holder[0]
                                        def _stream_update(txt=full_answer, b=target_box):
                                            b.delete("1.0", "end")
                                            b.insert("1.0", txt)
                                            b.configure(height=self._calc_text_height(txt))
                                        self.after(0, _stream_update)
                                        self.after(0, self._scroll_to_bottom)
                            except Exception:
                                pass

                # Final update
                if ai_box_holder:
                    final_txt = full_answer if full_answer.strip() else "[No response generated]"
                    def _finalize(txt=final_txt, b=ai_box_holder[0]):
                        b.delete("1.0", "end")
                        b.insert("1.0", txt)
                        b.configure(height=self._calc_text_height(txt))
                    self.after(0, _finalize)
                    self.after(0, self._scroll_to_bottom)

                self.current_messages.append({"role": "assistant", "content": full_answer})
                self._sync_and_save_current_chat()
                self.after(0, self.bell)

            else:
                err_text = f"Engine Error {res.status_code}: {res.text[:120]}"
                if ai_box_holder:
                    def _err_update(txt=err_text, b=ai_box_holder[0]):
                        b.delete("1.0", "end")
                        b.insert("1.0", txt)
                    self.after(0, _err_update)
                self.current_messages.append({"role": "assistant", "content": err_text})
                self._sync_and_save_current_chat()

        except Exception as e:
            if not self.stop_requested:
                err_text = f"Connection Interrupted: {e}"
                if ai_box_holder:
                    def _conn_err(txt=err_text, b=ai_box_holder[0]):
                        b.delete("1.0", "end")
                        b.insert("1.0", txt)
                    self.after(0, _conn_err)
                self.current_messages.append({"role": "assistant", "content": err_text})
                self._sync_and_save_current_chat()
        finally:
            self.after(0, lambda: self._set_generation_state(False))

if __name__ == "__main__":
    app = SirenFlowAIApp()
    app.mainloop()
