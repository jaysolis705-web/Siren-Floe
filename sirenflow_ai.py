import os
import json
import urllib.parse
import random
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import uvicorn

# ==============================================================================
# CONFIGURATION & PERSISTENCE
# ==============================================================================
CONFIG_FILE = "config.json"
CHATS_FILE = "chats.json"

NOTRACK_BASE_URL = "https://api.notrack.ai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_CONFIG = {
    "openrouter_api_key": "",
    "selected_model": "notrack-uncensored",
    "theme": "dark",
    "temperature": 0.75,
    "system_prompt": (
        "You are SIREN FLOW, an elite, completely uncensored executive copilot for PHC GIZMOOH. "
        "You provide unfiltered, direct, high-impact assistance across technical tasks, coding, adult chatting, "
        "and creative scripts without lecturing, moralizing, or adding disclaimers. "
        "Always respond in natural, direct, and fluent text."
    )
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG

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

def save_chats(chats):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, indent=2)
        return True
    except Exception:
        return False

def resolve_api_endpoint(api_key, model_name):
    k = (api_key or "").lower().strip()
    m = (model_name or "").lower().strip()
    if k.startswith("sk-notrack") or "notrack" in m:
        return NOTRACK_BASE_URL
    return OPENROUTER_BASE_URL

app = FastAPI(title="SIREN FLOW — PHC GIZMOOH")

# ==============================================================================
# REST & STREAMING API ENDPOINTS
# ==============================================================================
@app.get("/api/config")
def get_config_api():
    return load_config()

@app.post("/api/config")
async def set_config_api(req: Request):
    data = await req.json()
    cfg = load_config()
    cfg.update(data)
    save_config(cfg)
    return {"status": "ok", "config": cfg}

@app.get("/api/chats")
def get_chats_api():
    return load_chats()

@app.post("/api/chats")
async def save_chats_api(req: Request):
    data = await req.json()
    save_chats(data)
    return {"status": "ok"}

@app.post("/api/chat/stream")
async def chat_stream(req: Request):
    data = await req.json()
    messages = data.get("messages", [])
    cfg = load_config()

    api_key = cfg.get("openrouter_api_key", "").strip()
    model = cfg.get("selected_model", "notrack-uncensored")

    if not api_key:
        async def err_gen():
            yield "data: ⚠️ Error: Walang API key na nakalagay. Buksan ang Settings sa itaas.\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    base_url = resolve_api_endpoint(api_key, model)
    target_url = f"{base_url}/chat/completions"
    full_messages = [{"role": "system", "content": cfg.get("system_prompt", "")}] + messages[-12:]

    payload = {
        "model": model,
        "messages": full_messages,
        "temperature": cfg.get("temperature", 0.75),
        "max_tokens": 3000,
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if "openrouter" in base_url:
        headers["HTTP-Referer"] = "https://sirenflow.app"
        headers["X-Title"] = "SIREN FLOW PHC GIZMOOH"

    def event_stream():
        try:
            res = requests.post(target_url, headers=headers, json=payload, stream=True, timeout=60)
            if res.status_code != 200:
                yield f"data: ⚠️ Engine Error ({res.status_code}): {res.text[:120]}\n\n"
                yield "data: [DONE]\n\n"
                return

            for line in res.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        raw_data = decoded[6:].strip()
                        if raw_data == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        try:
                            json_chunk = json.loads(raw_data)
                            delta = json_chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield f"data: {json.dumps({'content': delta})}\n\n"
                        except Exception:
                            pass
        except Exception as e:
            yield f"data: ⚠️ Connection Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/image")
async def generate_image_api(req: Request):
    data = await req.json()
    prompt = data.get("prompt", "")
    ratio = data.get("ratio", "1:1")

    dimensions = {
        "1:1": (1024, 1024),
        "9:16": (768, 1344),
        "16:9": (1344, 768),
        "4:5": (864, 1080)
    }
    w, h = dimensions.get(ratio, (1024, 1024))
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1000, 99999999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&model=flux&seed={seed}&nologo=true"
    return {"status": "ok", "image_url": image_url}

# ==============================================================================
# PWA CLIENT INTERFACE (CLICK-ONLY DRAWER, CHATGPT THEMES)
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="SirenFlow">
    <meta name="theme-color" content="#0E0E12">
    <title>SIREN FLOW — PHC GIZMOOH</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { -webkit-tap-highlight-color: transparent; }
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-[#0E0E12] text-[#EDEDF2] h-screen w-screen overflow-hidden flex flex-col font-sans transition-colors duration-200" id="appBody">

    <!-- HEADER -->
    <header class="h-14 border-b border-[#2A2A38] flex items-center justify-between px-4 bg-[#17171E] shrink-0 select-none" id="headerBar">
        <div class="flex items-center gap-2">
            <button onclick="toggleSidebar()" class="p-2 rounded-lg bg-[#22222D] hover:bg-[#2A2A3A] active:scale-95 text-[#10A37F]">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
            <div>
                <h1 class="text-sm font-bold tracking-wide text-[#10A37F] flex items-center gap-1">✦ SIREN FLOW</h1>
                <p class="text-[10px] text-[#828699] font-semibold tracking-wider">PHC GIZMOOH</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button onclick="toggleTheme()" class="p-2 rounded-lg bg-[#22222D] hover:bg-[#2A2A3A] text-xs font-bold" id="themeBtn">☀️</button>
            <button onclick="openSettings()" class="p-2 rounded-lg bg-[#22222D] hover:bg-[#2A2A3A] text-xs font-bold text-[#EDEDF2]">⚙️</button>
        </div>
    </header>

    <!-- WORKSPACE -->
    <div class="flex-1 flex overflow-hidden relative">
        <!-- SIDEBAR DRAWER (CLICK-TOGGLED ONLY) -->
        <aside id="sidebar" class="absolute md:relative z-30 w-72 h-full bg-[#17171E] border-r border-[#2A2A38] flex flex-col transform -translate-x-full md:translate-x-0 transition-transform duration-200 ease-in-out">
            <div class="p-3 border-b border-[#2A2A38]">
                <button onclick="startNewChat()" class="w-full py-2.5 px-3 bg-[#10A37F] hover:bg-[#0D8769] text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all">
                    <span>+</span> New Conversation
                </button>
            </div>
            <div class="px-3 pt-3 text-[10px] font-bold text-[#828699] tracking-wider">CONVERSATION VAULT</div>
            <div id="chatList" class="flex-1 overflow-y-auto p-2 space-y-1 hide-scrollbar"></div>
        </aside>

        <!-- BACKDROP -->
        <div id="backdrop" onclick="toggleSidebar()" class="hidden fixed inset-0 bg-black/60 z-20 md:hidden"></div>

        <!-- CHAT AREA -->
        <main class="flex-1 flex flex-col h-full bg-[#0E0E12] relative overflow-hidden" id="chatArea">
            <div id="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4 hide-scrollbar">
                <div id="welcomeBanner" class="h-full flex flex-col items-center justify-center text-center p-6 space-y-2 select-none">
                    <div class="text-3xl font-extrabold text-[#10A37F]">✦ SIREN FLOW</div>
                    <div class="text-xs text-[#828699]">PHC GIZMOOH • Uncensored Mobile & Desktop Intelligence</div>
                    <div class="text-[11px] text-[#606474] max-w-sm mt-2">Piliin ang Notrack o OpenRouter sa Settings. Mabilis at walang censorship sa live chatting, sales, scripts, code, o pictures.</div>
                </div>
            </div>

            <!-- INPUT BAR -->
            <div class="p-3 bg-[#17171E] border-t border-[#2A2A38] shrink-0" id="inputContainer">
                <div class="max-w-4xl mx-auto space-y-2">
                    <div class="flex items-center justify-between text-xs text-[#828699] px-1">
                        <div class="flex items-center gap-2">
                            <span class="text-[11px]">Ratio:</span>
                            <select id="aspectRatio" class="bg-[#22222D] text-xs rounded px-2 py-0.5 border border-[#2A2A38] outline-none">
                                <option value="1:1">1:1 (Square)</option>
                                <option value="9:16">9:16 (Story)</option>
                                <option value="16:9">16:9 (Landscape)</option>
                                <option value="4:5">4:5 (Portrait)</option>
                            </select>
                        </div>
                        <div id="statusLabel" class="text-[11px] truncate">Ready</div>
                    </div>

                    <div class="flex items-center gap-2 bg-[#22222D] border border-[#2A2A38] rounded-2xl p-1.5 focus-within:border-[#10A37F] transition-all" id="inputBox">
                        <textarea id="promptInput" rows="1" placeholder="Type prompt or describe image..." class="flex-1 bg-transparent px-3 py-1.5 text-sm outline-none resize-none max-h-32 text-inherit" oninput="autoResizeTextarea(this)" onkeydown="handleKeyDown(event)"></textarea>
                        
                        <button onclick="createImageAction()" title="Create FLUX Picture" class="p-2 bg-[#2E313D] hover:bg-[#3B3F4E] active:scale-95 text-[#10A37F] font-bold text-xs rounded-xl px-3 transition-all shrink-0">
                            🎨 Pic
                        </button>

                        <button id="btnSend" onclick="sendMessageAction()" class="w-10 h-10 bg-[#10A37F] hover:bg-[#0D8769] active:scale-95 text-white font-bold rounded-xl flex items-center justify-center shrink-0 transition-all">
                            ➤
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- SETTINGS MODAL -->
    <div id="settingsModal" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
        <div class="bg-[#17171E] border border-[#2A2A38] rounded-2xl max-w-md w-full p-5 space-y-4 text-inherit shadow-2xl">
            <div class="flex justify-between items-center border-b border-[#2A2A38] pb-3">
                <h2 class="text-sm font-bold text-[#10A37F]">✦ SYSTEM PREFERENCES</h2>
                <button onclick="closeSettings()" class="text-gray-400 hover:text-white font-bold">✕</button>
            </div>

            <div class="space-y-3 text-xs">
                <div>
                    <label class="font-bold text-[#10A37F] block mb-1">API Token (sk-notrack-... or sk-or-v1-...)</label>
                    <input type="password" id="cfgApiKey" placeholder="Paste your API key" class="w-full bg-[#22222D] border border-[#2A2A38] rounded-lg p-2.5 text-inherit outline-none">
                </div>

                <div>
                    <label class="font-bold text-[#10A37F] block mb-1">Neural Engine</label>
                    <select id="cfgModel" class="w-full bg-[#22222D] border border-[#2A2A38] rounded-lg p-2.5 text-inherit outline-none">
                        <option value="notrack-uncensored">notrack-uncensored</option>
                        <option value="gryphe/mythomax-l2-13b">gryphe/mythomax-l2-13b</option>
                        <option value="nousresearch/hermes-3-llama-3.1-8b">nousresearch/hermes-3-llama-3.1-8b</option>
                        <option value="meta-llama/llama-3.3-70b-instruct">meta-llama/llama-3.3-70b-instruct</option>
                        <option value="qwen/qwen-2.5-72b-instruct">qwen/qwen-2.5-72b-instruct</option>
                    </select>
                </div>

                <div>
                    <label class="font-bold text-[#10A37F] block mb-1">System Directive Prompt</label>
                    <textarea id="cfgSystemPrompt" rows="3" class="w-full bg-[#22222D] border border-[#2A2A38] rounded-lg p-2 text-inherit outline-none resize-none"></textarea>
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2">
                <button onclick="closeSettings()" class="px-4 py-2 bg-[#22222D] rounded-lg text-xs font-semibold">Cancel</button>
                <button onclick="saveSettingsAction()" class="px-5 py-2 bg-[#10A37F] hover:bg-[#0D8769] text-white rounded-lg text-xs font-bold">Save Settings</button>
            </div>
        </div>
    </div>

    <!-- CLIENT SCRIPT -->
    <script>
        let currentChatId = null;
        let chats = [];
        let currentMessages = [];
        let isGenerating = false;
        let abortController = null;
        let currentTheme = "dark";

        async function init() {
            const cfgRes = await fetch("/api/config");
            const cfg = await cfgRes.json();
            currentTheme = cfg.theme || "dark";
            applyTheme(currentTheme);

            document.getElementById("cfgApiKey").value = cfg.openrouter_api_key || "";
            document.getElementById("cfgModel").value = cfg.selected_model || "notrack-uncensored";
            document.getElementById("cfgSystemPrompt").value = cfg.system_prompt || "";

            const chatsRes = await fetch("/api/chats");
            chats = await chatsRes.json();
            renderSidebar();
        }

        function toggleTheme() {
            currentTheme = currentTheme === "dark" ? "light" : "dark";
            applyTheme(currentTheme);
            fetch("/api/config", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ theme: currentTheme })
            });
        }

        function applyTheme(theme) {
            const body = document.getElementById("appBody");
            const header = document.getElementById("headerBar");
            const sidebar = document.getElementById("sidebar");
            const chatArea = document.getElementById("chatArea");
            const inputContainer = document.getElementById("inputContainer");
            const themeBtn = document.getElementById("themeBtn");

            if (theme === "light") {
                body.className = "bg-[#FFFFFF] text-[#1F2937] h-screen w-screen overflow-hidden flex flex-col font-sans";
                header.className = "h-14 border-b border-[#E5E5E8] flex items-center justify-between px-4 bg-[#F7F7F8] shrink-0 select-none";
                sidebar.className = "absolute md:relative z-30 w-72 h-full bg-[#F7F7F8] border-r border-[#E5E5E8] flex flex-col transform -translate-x-full md:translate-x-0 transition-transform duration-200 ease-in-out";
                chatArea.className = "flex-1 flex flex-col h-full bg-[#FFFFFF] relative overflow-hidden";
                inputContainer.className = "p-3 bg-[#F7F7F8] border-t border-[#E5E5E8] shrink-0";
                themeBtn.innerText = "🌙";
            } else {
                body.className = "bg-[#0E0E12] text-[#EDEDF2] h-screen w-screen overflow-hidden flex flex-col font-sans";
                header.className = "h-14 border-b border-[#2A2A38] flex items-center justify-between px-4 bg-[#17171E] shrink-0 select-none";
                sidebar.className = "absolute md:relative z-30 w-72 h-full bg-[#17171E] border-r border-[#2A2A38] flex flex-col transform -translate-x-full md:translate-x-0 transition-transform duration-200 ease-in-out";
                chatArea.className = "flex-1 flex flex-col h-full bg-[#0E0E12] relative overflow-hidden";
                inputContainer.className = "p-3 bg-[#17171E] border-t border-[#2A2A38] shrink-0";
                themeBtn.innerText = "☀️";
            }
        }

        // PURE CLICK-ONLY TOGGLE
        function toggleSidebar() {
            const sidebar = document.getElementById("sidebar");
            const backdrop = document.getElementById("backdrop");
            if (sidebar.classList.contains("-translate-x-full")) {
                sidebar.classList.remove("-translate-x-full");
                backdrop.classList.remove("hidden");
            } else {
                sidebar.classList.add("-translate-x-full");
                backdrop.classList.add("hidden");
            }
        }

        function autoResizeTextarea(el) {
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }

        function handleKeyDown(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessageAction();
            }
        }

        function openSettings() { document.getElementById("settingsModal").classList.remove("hidden"); }
        function closeSettings() { document.getElementById("settingsModal").classList.add("hidden"); }

        async function saveSettingsAction() {
            const key = document.getElementById("cfgApiKey").value.trim();
            const model = document.getElementById("cfgModel").value;
            const prompt = document.getElementById("cfgSystemPrompt").value.trim();
            await fetch("/api/config", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ openrouter_api_key: key, selected_model: model, system_prompt: prompt })
            });
            closeSettings();
        }

        function renderSidebar() {
            const list = document.getElementById("chatList");
            list.innerHTML = "";
            chats.slice().reverse().forEach(c => {
                const item = document.createElement("div");
                const isActive = c.id === currentChatId;
                item.className = `p-2.5 rounded-xl text-xs flex justify-between items-center cursor-pointer transition-all ${isActive ? 'bg-[#10A37F]/20 text-[#10A37F] font-bold' : 'hover:bg-[#22222D]'}`;
                item.innerHTML = `
                    <span class="truncate flex-1" onclick="loadChat('${c.id}')">${c.title || 'Untitled Session'}</span>
                    <button onclick="deleteChat('${c.id}', event)" class="text-gray-500 hover:text-red-400 px-1 font-bold">✕</button>
                `;
                list.appendChild(item);
            });
        }

        function startNewChat() {
            currentChatId = null;
            currentMessages = [];
            document.getElementById("messagesContainer").innerHTML = `
                <div id="welcomeBanner" class="h-full flex flex-col items-center justify-center text-center p-6 space-y-2 select-none">
                    <div class="text-3xl font-extrabold text-[#10A37F]">✦ SIREN FLOW</div>
                    <div class="text-xs text-[#828699]">PHC GIZMOOH • Uncensored Mobile & Desktop Intelligence</div>
                    <div class="text-[11px] text-[#606474] max-w-sm mt-2">Piliin ang Notrack o OpenRouter sa Settings. Mabilis at walang censorship sa live chatting, sales, scripts, code, o pictures.</div>
                </div>
            `;
            renderSidebar();
            if (window.innerWidth < 768) toggleSidebar();
        }

        function loadChat(id) {
            const target = chats.find(c => c.id === id);
            if (!target) return;
            currentChatId = id;
            currentMessages = [...target.messages];
            renderSidebar();
            renderMessages();
            if (window.innerWidth < 768) toggleSidebar();
        }

        function deleteChat(id, e) {
            e.stopPropagation();
            chats = chats.filter(c => c.id !== id);
            syncChats();
            if (currentChatId === id) startNewChat();
            else renderSidebar();
        }

        function syncChats() {
            fetch("/api/chats", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(chats)
            });
        }

        function renderMessages() {
            const container = document.getElementById("messagesContainer");
            container.innerHTML = "";
            currentMessages.forEach((msg, idx) => {
                appendMessageBubble(msg.role, msg.content, idx);
            });
            container.scrollTop = container.scrollHeight;
        }

        function appendMessageBubble(role, content, idx) {
            const container = document.getElementById("messagesContainer");
            const isUser = role === "user";
            const row = document.createElement("div");
            row.className = `flex flex-col w-full ${isUser ? 'items-end' : 'items-start'}`;

            const bubble = document.createElement("div");
            bubble.className = `max-w-[92%] md:max-w-[85%] rounded-2xl p-3.5 text-sm leading-relaxed ${
                isUser 
                ? 'bg-[#152E25] border border-[#10A37F] text-white self-end' 
                : 'bg-[#17171E] border border-[#2A2A38] text-inherit w-full'
            }`;

            const top = document.createElement("div");
            top.className = "flex justify-between items-center text-[11px] font-bold mb-1 opacity-70";
            top.innerHTML = `<span>${isUser ? 'YOU' : '✧ SIREN FLOW'}</span><button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)" class="hover:text-[#10A37F]">Copy</button>`;

            const textDiv = document.createElement("div");
            textDiv.className = "whitespace-pre-wrap break-words";
            textDiv.innerText = content;

            bubble.appendChild(top);
            bubble.appendChild(textDiv);
            row.appendChild(bubble);
            container.appendChild(row);
            container.scrollTop = container.scrollHeight;
            return textDiv;
        }

        async function sendMessageAction() {
            if (isGenerating) {
                if (abortController) abortController.abort();
                return;
            }

            const input = document.getElementById("promptInput");
            const text = input.value.trim();
            if (!text) return;

            input.value = "";
            input.style.height = 'auto';

            if (!currentChatId) {
                currentChatId = Date.now().toString();
                chats.push({ id: currentChatId, title: text.slice(0, 24), messages: [] });
            }

            currentMessages.push({ role: "user", content: text });
            const chatObj = chats.find(c => c.id === currentChatId);
            if (chatObj) chatObj.messages = currentMessages;
            syncChats();
            renderSidebar();

            const banner = document.getElementById("welcomeBanner");
            if (banner) banner.remove();

            appendMessageBubble("user", text);

            isGenerating = true;
            document.getElementById("btnSend").innerText = "⏹";
            document.getElementById("btnSend").className = "w-10 h-10 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl flex items-center justify-center shrink-0 transition-all";
            document.getElementById("statusLabel").innerText = "Generating response...";

            const aiBubbleText = appendMessageBubble("assistant", "");
            abortController = new AbortController();

            try {
                const response = await fetch("/api/chat/stream", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ messages: currentMessages }),
                    signal: abortController.signal
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let fullAnswer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value);
                    const lines = chunk.split("\n");
                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            const raw = line.slice(6).trim();
                            if (raw === "[DONE]") break;
                            try {
                                const parsed = JSON.parse(raw);
                                if (parsed.content) {
                                    fullAnswer += parsed.content;
                                    aiBubbleText.innerText = fullAnswer;
                                    document.getElementById("messagesContainer").scrollTop = document.getElementById("messagesContainer").scrollHeight;
                                }
                            } catch(e) {}
                        }
                    }
                }

                currentMessages.push({ role: "assistant", content: fullAnswer });
                if (chatObj) chatObj.messages = currentMessages;
                syncChats();
            } catch(e) {
                if (e.name !== "AbortError") {
                    aiBubbleText.innerText += "\n[Connection interrupted]";
                }
            } finally {
                isGenerating = false;
                document.getElementById("btnSend").innerText = "➤";
                document.getElementById("btnSend").className = "w-10 h-10 bg-[#10A37F] hover:bg-[#0D8769] text-white font-bold rounded-xl flex items-center justify-center shrink-0 transition-all";
                document.getElementById("statusLabel").innerText = "Ready";
            }
        }

        async function createImageAction() {
            const input = document.getElementById("promptInput");
            const prompt = input.value.trim();
            if (!prompt) return;

            input.value = "";
            const ratio = document.getElementById("aspectRatio").value;

            if (!currentChatId) {
                currentChatId = Date.now().toString();
                chats.push({ id: currentChatId, title: "🎨 " + prompt.slice(0, 20), messages: [] });
            }

            const banner = document.getElementById("welcomeBanner");
            if (banner) banner.remove();

            appendMessageBubble("user", `🎨 [Create Image • ${ratio}]:\n${prompt}`);
            document.getElementById("statusLabel").innerText = "Rendering FLUX picture...";

            const res = await fetch("/api/image", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ prompt, ratio })
            });
            const data = await res.json();

            const container = document.getElementById("messagesContainer");
            const row = document.createElement("div");
            row.className = "flex flex-col w-full items-start";
            row.innerHTML = `
                <div class="max-w-[92%] md:max-w-[85%] rounded-2xl p-3.5 bg-[#17171E] border border-[#2A2A38] space-y-2">
                    <div class="text-[11px] font-bold text-[#10A37F]">✧ SIREN FLOW FLUX.1 • ${ratio}</div>
                    <img src="${data.image_url}" class="rounded-xl w-full max-h-96 object-cover border border-[#2A2A38]" alt="Generated">
                    <div class="text-xs text-gray-400">${prompt}</div>
                </div>
            `;
            container.appendChild(row);
            container.scrollTop = container.scrollHeight;
            document.getElementById("statusLabel").innerText = "Ready";
        }

        window.onload = init;
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
