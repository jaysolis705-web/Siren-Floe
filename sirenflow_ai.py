import os
import sys
import json
import threading
import platform
import datetime
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import requests
from PIL import Image, ImageTk

# ==============================================================================
# 1. LUXURY THEMES PALETTE SYSTEM
# ==============================================================================
THEMES = {
    "Champagne Gold": {
        "accent": "#D4AF37",
        "accent_hover": "#F3E5AB",
        "bg_root": "#08090B",
        "bg_sidebar": "#0D0E12",
        "bg_card": "#13151B",
        "user_bubble": "#211D15",
        "user_border": "#8C7326",
        "ai_bubble": "#12141A",
        "ai_border": "#282C37",
        "text_main": "#EDEDF2",
        "text_muted": "#828699"
    },
    "Cyberpunk Cyan": {
        "accent": "#00F0FF",
        "accent_hover": "#70F8FF",
        "bg_root": "#06090E",
        "bg_sidebar": "#090E17",
        "bg_card": "#101622",
        "user_bubble": "#0C232B",
        "user_border": "#009AA3",
        "ai_bubble": "#0D131D",
        "ai_border": "#1D283A",
        "text_main": "#F0F6FC",
        "text_muted": "#7B889B"
    },
    "Emerald Velvet": {
        "accent": "#2ECC71",
        "accent_hover": "#58D68D",
        "bg_root": "#060B08",
        "bg_sidebar": "#0A120D",
        "bg_card": "#101B14",
        "user_bubble": "#102619",
        "user_border": "#1E8449",
        "ai_bubble": "#0E1711",
        "ai_border": "#1E2F23",
        "text_main": "#E8F8F5",
        "text_muted": "#769A85"
    },
    "Royal Amethyst": {
        "accent": "#A855F7",
        "accent_hover": "#C084FC",
        "bg_root": "#0A0710",
        "bg_sidebar": "#0E0A17",
        "bg_card": "#171224",
        "user_bubble": "#25143A",
        "user_border": "#7E22CE",
        "ai_bubble": "#120E1C",
        "ai_border": "#271E3A",
        "text_main": "#F5F3FF",
        "text_muted": "#897E9C"
    },
    "Crimson Noir": {
        "accent": "#EF4444",
        "accent_hover": "#F87171",
        "bg_root": "#0D0708",
        "bg_sidebar": "#140A0C",
        "bg_card": "#1C1012",
        "user_bubble": "#2E1114",
        "user_border": "#B91C1C",
        "ai_bubble": "#170D0F",
        "ai_border": "#311B1E",
        "text_main": "#FEF2F2",
        "text_muted": "#96787B"
    }
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
        "wallpaper_path": "",
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
            return json.load(f)
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
# 3. EXECUTIVE PREFERENCES MODAL
# ==============================================================================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.title("SirenFlow AI — Preferences & Themes")
        self.geometry("540x580")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        t = parent.theme
        self.configure(fg_color=t["bg_root"])
        ctk.set_appearance_mode("dark")

        self.cfg = load_config()

        ctk.CTkLabel(
            self, text="✦ SYSTEM & VISUAL PREFERENCES",
            font=(FONT_FAMILY, 13, "bold"), text_color=t["accent"]
        ).pack(pady=(16, 2))
        
        ctk.CTkLabel(
            self, text="Configure Neural Engines, Themes & Wallpaper Customization",
            font=(FONT_FAMILY, 9), text_color=t["text_muted"]
        ).pack(pady=(0, 10))

        frame = ctk.CTkScrollableFrame(
            self, fg_color=t["bg_card"], corner_radius=10,
            border_width=1, border_color=t["ai_border"]
        )
        frame.pack(fill="both", expand=True, padx=20, pady=4)

        # API Key
        ctk.CTkLabel(frame, text="OpenRouter API Token:", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=12, pady=(8, 2))
        self.entry_key = ctk.CTkEntry(frame, show="*", font=(FONT_FAMILY, 10), height=30, fg_color=t["bg_root"], text_color=t["text_main"], placeholder_text="sk-or-v1-...")
        self.entry_key.insert(0, self.cfg.get("openrouter_api_key", ""))
        self.entry_key.pack(fill="x", padx=12, pady=(0, 8))

        # Model Selector
        ctk.CTkLabel(frame, text="Neural Engine (Preloaded Uncensored Models):", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=12, pady=(4, 2))
        self.combo_model = ctk.CTkComboBox(frame, values=POPULAR_MODELS, height=30, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"])
        self.combo_model.set(self.cfg.get("selected_model", POPULAR_MODELS[0]))
        self.combo_model.pack(fill="x", padx=12, pady=(0, 8))

        # Theme Picker
        ctk.CTkLabel(frame, text="Visual Aesthetic Theme:", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=12, pady=(4, 2))
        self.combo_theme = ctk.CTkComboBox(frame, values=list(THEMES.keys()), height=30, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"])
        self.combo_theme.set(self.cfg.get("selected_theme", "Champagne Gold"))
        self.combo_theme.pack(fill="x", padx=12, pady=(0, 8))

        # Wallpaper Picture Selector
        ctk.CTkLabel(frame, text="Custom Chat Wallpaper (Picture Background):", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=12, pady=(4, 2))
        wall_row = ctk.CTkFrame(frame, fg_color="transparent")
        wall_row.pack(fill="x", padx=12, pady=(0, 8))

        self.lbl_wall = ctk.CTkLabel(wall_row, text=os.path.basename(self.cfg.get("wallpaper_path", "")) or "No custom picture selected", font=(FONT_FAMILY, 8), text_color=t["text_muted"])
        self.lbl_wall.pack(side="left", padx=(0, 8))

        self.temp_wall_path = self.cfg.get("wallpaper_path", "")
        btn_upload = ctk.CTkButton(wall_row, text="📁 Choose Pic", width=95, height=26, font=(FONT_FAMILY, 8, "bold"), fg_color="#242634", hover_color="#36394C", command=self._pick_wallpaper)
        btn_upload.pack(side="right", padx=2)

        btn_clear_wall = ctk.CTkButton(wall_row, text="✕ Clear", width=65, height=26, font=(FONT_FAMILY, 8), fg_color="#381E22", hover_color="#54252B", command=self._clear_wallpaper)
        btn_clear_wall.pack(side="right", padx=2)

        # System Prompt
        ctk.CTkLabel(frame, text="System Prompt (Persona, Persona Rules):", font=(FONT_FAMILY, 9, "bold"), text_color=t["accent"]).pack(anchor="w", padx=12, pady=(4, 2))
        self.txt_sys = ctk.CTkTextbox(frame, height=95, font=(FONT_FAMILY, 9), fg_color=t["bg_root"], text_color=t["text_main"], wrap="word")
        self.txt_sys.insert("1.0", self.cfg.get("system_prompt", ""))
        self.txt_sys.pack(fill="x", padx=12, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=(FONT_FAMILY, 9), text_color=t["accent"])
        self.lbl_status.pack(pady=2)

        btn_save = ctk.CTkButton(
            self, text="APPLY PREFERENCES & REFRESH THEME", font=(FONT_FAMILY, 10, "bold"), height=36,
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#08090B", corner_radius=8, command=self._save
        )
        btn_save.pack(fill="x", padx=20, pady=(0, 14))

    def _pick_wallpaper(self):
        file_path = filedialog.askopenfilename(
            title="Select Chat Wallpaper Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")]
        )
        if file_path:
            self.temp_wall_path = file_path
            self.lbl_wall.configure(text=os.path.basename(file_path))

    def _clear_wallpaper(self):
        self.temp_wall_path = ""
        self.lbl_wall.configure(text="No custom picture selected")

    def _save(self):
        self.cfg["openrouter_api_key"] = self.entry_key.get().strip()
        self.cfg["selected_model"] = self.combo_model.get().strip()
        self.cfg["selected_theme"] = self.combo_theme.get().strip()
        self.cfg["wallpaper_path"] = self.temp_wall_path
        self.cfg["system_prompt"] = self.txt_sys.get("1.0", "end").strip()
        save_config(self.cfg)
        
        self.parent.cfg = self.cfg
        self.parent.apply_theme_and_rebuild()
        self.lbl_status.configure(text="✔ Preferences applied! Refreshing layout...")
        self.after(500, self.destroy)

# ==============================================================================
# 4. MAIN APPLICATION WINDOW WITH CHAT BUBBLES
# ==============================================================================
class SirenFlowAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SirenFlow AI — Private Luxury Edition")
        self.geometry("980x700")
        self.minsize(800, 550)
        ctk.set_appearance_mode("dark")

        self.cfg = load_config()
        self.theme_name = self.cfg.get("selected_theme", "Champagne Gold")
        self.theme = THEMES.get(self.theme_name, THEMES["Champagne Gold"])

        self.chats = load_chats()
        self.current_chat_id = None
        self.current_messages = []
        self.bg_photo_image = None

        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.start_new_chat(render_welcome=True)

    def apply_theme_and_rebuild(self):
        self.theme_name = self.cfg.get("selected_theme", "Champagne Gold")
        self.theme = THEMES.get(self.theme_name, THEMES["Champagne Gold"])
        
        # Linisin at buuin muli ang UI
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
            top_bar, text="⚙️ Preferences", width=95, height=26, font=(FONT_FAMILY, 9),
            fg_color="#151722", hover_color="#232637", text_color=t["text_main"],
            border_width=1, border_color=t["ai_border"], corner_radius=6,
            command=lambda: SettingsWindow(self)
        )
        btn_settings.pack(side="right", padx=14, pady=8)

        # Chat Backdrop & Wallpaper Container
        self.chat_container = ctk.CTkFrame(self.main_frame, fg_color=t["bg_root"], corner_radius=0)
        self.chat_container.pack(fill="both", expand=True)

        self._apply_wallpaper()

        # ChatGPT-Style Scrollable Messages Frame
        self.scroll_messages = ctk.CTkScrollableFrame(self.chat_container, fg_color="transparent")
        self.scroll_messages.pack(fill="both", expand=True, padx=8, pady=4)

        # Input Bar
        input_container = ctk.CTkFrame(self.main_frame, fg_color=t["bg_card"], corner_radius=10, border_width=1, border_color=t["ai_border"])
        input_container.pack(fill="x", side="bottom", padx=16, pady=(4, 14))

        self.entry_user = ctk.CTkEntry(
            input_container, placeholder_text="Ask anything or generate extensive scripts...",
            font=(FONT_FAMILY, 10), height=42, fg_color="transparent",
            text_color=t["text_main"], border_width=0
        )
        self.entry_user.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=4)
        self.entry_user.bind("<Return>", lambda e: self.send_message())

        self.btn_send = ctk.CTkButton(
            input_container, text="➤", width=42, height=36, font=(FONT_FAMILY, 13, "bold"),
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#08090B", corner_radius=8, command=self.send_message
        )
        self.btn_send.pack(side="right", padx=(0, 6), pady=4)

        self._refresh_sidebar_list()

    def _apply_wallpaper(self):
        wall_path = self.cfg.get("wallpaper_path", "")
        if wall_path and os.path.exists(wall_path):
            try:
                pil_img = Image.open(wall_path)
                pil_img = pil_img.resize((1400, 900), Image.Resampling.LANCZOS)
                self.bg_photo_image = ImageTk.PhotoImage(pil_img)
                bg_lbl = tk.Label(self.chat_container, image=self.bg_photo_image, borderwidth=0)
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                pass

    # -------------------------------------------------------------
    # CHAT BUBBLES RENDER ENGINE (CHATGPT LOOK)
    # -------------------------------------------------------------
    def _create_bubble(self, role, content):
        t = self.theme
        is_user = (role == "user")

        row = ctk.CTkFrame(self.scroll_messages, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)

        if is_user:
            # User Bubble: Aligned Right
            bubble = ctk.CTkFrame(
                row, fg_color=t["user_bubble"], corner_radius=12,
                border_width=1, border_color=t["user_border"]
            )
            bubble.pack(anchor="e", padx=(80, 8))

            header = ctk.CTkLabel(bubble, text="YOU", font=(FONT_FAMILY, 8, "bold"), text_color=t["accent"])
            header.pack(anchor="w", padx=12, pady=(6, 2))

            msg_lbl = ctk.CTkLabel(
                bubble, text=content, font=(FONT_FAMILY, 9),
                text_color=t["text_main"], justify="left", wraplength=480
            )
            msg_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        else:
            # Assistant Bubble: Sleek Left Card with Copy Button
            bubble = ctk.CTkFrame(
                row, fg_color=t["ai_bubble"], corner_radius=12,
                border_width=1, border_color=t["ai_border"]
            )
            bubble.pack(anchor="w", padx=(8, 80))

            card_head = ctk.CTkFrame(bubble, fg_color="transparent")
            card_head.pack(fill="x", padx=12, pady=(6, 2))

            header = ctk.CTkLabel(card_head, text="✧ SIRENFLOW", font=(FONT_FAMILY, 8, "bold"), text_color=t["accent"])
            header.pack(side="left")

            btn_copy = ctk.CTkButton(
                card_head, text="📋 Copy", width=50, height=18,
                font=(FONT_FAMILY, 7, "bold"), fg_color="#181A22",
                hover_color="#2B2E3D", text_color=t["text_muted"],
                corner_radius=4, command=lambda c=content: self._copy_to_clipboard(c)
            )
            btn_copy.pack(side="right")

            msg_lbl = ctk.CTkLabel(
                bubble, text=content, font=(FONT_FAMILY, 9),
                text_color=t["text_main"], justify="left", wraplength=520
            )
            msg_lbl.pack(anchor="w", padx=12, pady=(2, 10))

        self._scroll_to_bottom()

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.bell()

    def _scroll_to_bottom(self):
        self.scroll_messages._parent_canvas.yview_moveto(1.0)

    # -------------------------------------------------------------
    # SESSIONS & HISTORY VAULT
    # -------------------------------------------------------------
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
                corner_radius=6, height=30
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            btn_chat = ctk.CTkButton(
                row, text=title, anchor="w", font=(FONT_FAMILY, 9),
                text_color=t["accent"] if is_active else t["text_main"],
                fg_color="transparent", hover_color="#1D202B",
                command=lambda cid=chat_id: self.load_chat_by_id(cid)
            )
            btn_chat.pack(side="left", fill="both", expand=True, padx=(6, 0))

            btn_del = ctk.CTkButton(
                row, text="✕", width=20, height=20, font=(FONT_FAMILY, 8, "bold"),
                fg_color="transparent", hover_color="#4C181E", text_color="#6A6F82",
                corner_radius=4, command=lambda cid=chat_id: self.delete_chat_by_id(cid)
            )
            btn_del.pack(side="right", padx=(0, 6))

    def start_new_chat(self, render_welcome=True):
        self.current_chat_id = None
        self.current_messages = []
        self._refresh_sidebar_list()

        for widget in self.scroll_messages.winfo_children():
            widget.destroy()

        if render_welcome:
            welcome_text = (
                "Welcome to SirenFlow AI Private Edition.\n\n"
                "• Completely uncensored dialogue & multi-turn memory.\n"
                "• 3,000 token capacity for full-length scripts & storytelling.\n"
                "• Customizable luxury themes & wallpaper support."
            )
            self._create_bubble("assistant", welcome_text)

    def load_chat_by_id(self, chat_id):
        target = next((c for c in self.chats if c["id"] == chat_id), None)
        if not target:
            return

        self.current_chat_id = chat_id
        self.current_messages = target.get("messages", [])
        self._refresh_sidebar_list()

        for widget in self.scroll_messages.winfo_children():
            widget.destroy()

        for msg in self.current_messages:
            self._create_bubble(msg["role"], msg["content"])

    def delete_chat_by_id(self, chat_id):
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        save_chats(self.chats)
        if self.current_chat_id == chat_id:
            self.start_new_chat(render_welcome=True)
        else:
            self._refresh_sidebar_list()

    # -------------------------------------------------------------
    # MESSAGING & OPENROUTER ENGINE
    # -------------------------------------------------------------
    def send_message(self):
        query = self.entry_user.get().strip()
        if not query:
            return

        self.entry_user.delete(0, "end")
        self._create_bubble("user", query)
        self.btn_send.configure(state="disabled")

        if self.current_chat_id is None:
            self.current_chat_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            title_snippet = query[:20] + "..." if len(query) > 20 else query
            new_session = {
                "id": self.current_chat_id,
                "title": title_snippet,
                "created_at": datetime.datetime.now().isoformat(),
                "messages": []
            }
            self.chats.append(new_session)
            self._refresh_sidebar_list()

        threading.Thread(target=self._query_openrouter, args=(query,), daemon=True).start()

    def _query_openrouter(self, user_msg):
        api_key = self.cfg.get("openrouter_api_key", "").strip()
        if not api_key:
            self.after(0, lambda: self._create_bubble("assistant", "⚠️ Warning: OpenRouter API Key is empty! Open ⚙️ Preferences to authenticate."))
            self.after(0, lambda: self.btn_send.configure(state="normal"))
            return

        self.current_messages.append({"role": "user", "content": user_msg})

        messages = [{"role": "system", "content": self.cfg.get("system_prompt", "")}]
        messages.extend(self.current_messages[-10:])

        payload = {
            "model": self.cfg.get("selected_model", "gryphe/mythomax-l2-13b"),
            "messages": messages,
            "temperature": self.cfg.get("temperature", 0.75),
            "max_tokens": 3000
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://sirenflow.app",
            "X-Title": "SirenFlow Desktop",
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(f"{OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=50)
            if res.status_code == 200:
                answer = res.json()["choices"][0]["message"]["content"].strip()
                self.current_messages.append({"role": "assistant", "content": answer})

                for c in self.chats:
                    if c["id"] == self.current_chat_id:
                        c["messages"] = self.current_messages
                        break
                save_chats(self.chats)

                self.after(0, lambda: self._create_bubble("assistant", answer))
                self.after(0, self.bell)
            else:
                err_body = res.text[:120]
                self.after(0, lambda: self._create_bubble("assistant", f"⚠️ [Engine Error {res.status_code}]: {err_body}"))
        except Exception as e:
            self.after(0, lambda: self._create_bubble("assistant", f"⚠️ [Connection Interrupted]: {e}"))
        finally:
            self.after(0, lambda: self.btn_send.configure(state="normal"))

if __name__ == "__main__":
    app = SirenFlowAIApp()
    app.mainloop()
