// app/static/chat.js
import { encryptMessage, decryptMessage, initGlobalChatKey } from "./crypto-e2ee.js";

let ws;
let username = null;
let token = null;
let currentChatName = "global";
let onlineUsers = [];

// ================= UI Toggle =================
function showRegister() {
    loginSection(false);
    registerSection(true);
}
function showLogin() {
    registerSection(false);
    loginSection(true);
}
function loginSection(show) {
    document.getElementById("login-section").style.display = show ? "block" : "none";
}
function registerSection(show) {
    document.getElementById("register-section").style.display = show ? "block" : "none";
}

// ================= Register =================
async function register() {
    const username = document.getElementById("reg-username").value;
    const password = document.getElementById("reg-password").value;
    const email = document.getElementById("reg-email").value;

    const res = await fetch("/register/", {
        method: "POST",
        body: new URLSearchParams({ username, password, email })
    });

    if (res.ok) {
        alert("Registered successfully!");
        showLogin();
    } else {
        const err = await res.json();
        alert("Error: " + err.detail);
    }
}

// ================= Login =================
async function login() {
    username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    // 🔐 init global chat key
    try {
        await initGlobalChatKey();
        //console.log("[CHAT] Global chat key initialized");
    } catch (e) {
        console.error("E2EE init failed:", e);
        alert("رمزنگاری فعال نشد.");
        return;
    }

    // 🌐 login
    const res = await fetch("/login/", {
        method: "POST",
        body: new URLSearchParams({ username, password })
    });

    if (!res.ok) {
        alert("Login failed");
        return;
    }

    const data = await res.json();
    token = data.access_token;

    localStorage.setItem("token", token);
    localStorage.setItem("username", username);

    showChat();
    connectWS(currentChatName);
}

// ================= Show Chat =================
function showChat() {
    loginSection(false);
    registerSection(false);
    document.getElementById("chat-section").style.display = "block";
    document.getElementById("chat-user").textContent = username;

    renderOnlineUsers();
    loadMessages(currentChatName);
}

// ================= Logout =================
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    token = null;
    username = null;
    currentChatName = "global";
    onlineUsers = [];

    if (ws) {
        ws.onclose = null;
        ws.close();
        ws = null;
    }

    document.getElementById("messages").innerHTML = "";
    document.getElementById("message-input").value = "";
    document.getElementById("file-input").value = "";
    document.getElementById("chat-user").textContent = "";

    document.getElementById("chat-section").style.display = "none";
    registerSection(false);
    loginSection(true);
}

// ================= Load Messages =================
async function loadMessages(chatName = currentChatName) {
    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML = "";

    try {
        const res = await fetch(`/messages/?chat_id=${chatName}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            for (const msg of data.messages) {
                displayMessage(msg);
            }
        }
    } catch (e) {
        console.error("Error loading messages", e);
    }
}

// ================= WebSocket =================
function connectWS(chatName = currentChatName) {
    if (!token) return;

    if (ws && ws.readyState === WebSocket.OPEN) ws.close();

    const wsProto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${wsProto}://${location.host}/ws?token=${token}&chat_name=${chatName}`);

    ws.onmessage = e => {
        const msg = JSON.parse(e.data);

        if (msg.type === "online_users") {
            onlineUsers = msg.users;
            renderOnlineUsers();
        } else {
            displayMessage(msg);
        }
    };

    ws.onclose = () => {
        console.warn("WebSocket closed.");
    };
}

// ================= Send Message =================
async function sendMessage() {
    const input = document.getElementById("message-input");
    const fileInput = document.getElementById("file-input");

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("اتصال WebSocket برقرار نیست.");
        return;
    }

    // فایل
    if (fileInput.files.length) {
        const fd = new FormData();
        fd.append("file", fileInput.files[0]);
        const res = await fetch("/upload/", { method: "POST", body: fd });
        const data = await res.json();
        ws.send(JSON.stringify({ type: "file", text: data.file_url, chat_name: currentChatName }));
        fileInput.value = "";
    }

    // متن
    if (input.value.trim()) {
        try {
            const cipher = await encryptMessage(input.value);
            ws.send(JSON.stringify({ type: "text", text: cipher, chat_name: currentChatName }));
            input.value = "";
        } catch (e) {
            alert("رمزنگاری پیام انجام نشد: " + e);
        }
    }
}

// ================= Display Message =================
function displayMessage(msg) {
    const messages = document.getElementById("messages");
    const wrap = document.createElement("div");

    wrap.className = "message " + (msg.username === username ? "me" : "other");

    if (msg.type === "file") {
        let body = "";
        const url = msg.text;

        if (/\.(jpg|jpeg|png|gif|heic|jfif)$/i.test(url)) {
            body = `<img src="${url}" class="chat-image">`;
        } else if (/\.(mp4|mov|webm|ogg)$/i.test(url)) {
            body = `<video class="chat-video" controls playsinline><source src="${url}"></video>`;
        } else if (/\.pdf$/i.test(url)) {
            body = `<div class="pdf-box">📄 <a href="${url}" target="_blank">View PDF</a></div>`;
        } else {
            body = `<a href="${url}" target="_blank">Download file</a>`;
        }

        wrap.innerHTML = `<div class="sender">${msg.username}</div><div class="bubble">${body}</div><div class="time">${formatTime(msg.timestamp)}</div>`;
        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;
        return;
    }

    // متن
    wrap.innerHTML = `<div class="sender">${msg.username}</div><div class="bubble"><div class="text-message">(در حال بارگذاری…)</div></div><div class="time">${formatTime(msg.timestamp)}</div>`;
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;

    decryptMessage(msg.text)
        .then(plain => wrap.querySelector(".bubble").innerHTML = `<div class="text-message">${plain}</div>`)
        .catch(() => wrap.querySelector(".bubble").innerHTML = `<div class="text-message">(رمزنگشایی نشد)</div>`);
}

// ================= Online Users =================
function renderOnlineUsers() {
    const containerId = "online-users";
    let container = document.getElementById(containerId);

    if (!container) {
        container = document.createElement("div");
        container.id = containerId;
        container.style.cssText = "border-bottom:1px solid #ccc;padding:5px; max-height:50px; overflow-x:auto;";
        document.querySelector(".chat-container").prepend(container);
    }

    const usersHtml = onlineUsers.filter(u => u !== username)
        .map(u => `<span class="user-item" onclick="startPrivateChat('${u}')">${u}</span>`).join("");
    container.innerHTML = usersHtml;
}

// ================= Start Private Chat =================
function startPrivateChat(otherUser) {
    currentChatName = `private_${[username, otherUser].sort().join("_")}`;
    loadMessages(currentChatName);
    connectWS(currentChatName);
}

// ================= Helpers =================
function formatTime(ts) {
    return ts ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "";
}

// ================= Expose to HTML =================
window.login = login;
window.register = register;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.logout = logout;
window.sendMessage = sendMessage;
window.startPrivateChat = startPrivateChat;

// ================= Restore session =================
document.addEventListener("DOMContentLoaded", async () => {
    token = localStorage.getItem("token");
    username = localStorage.getItem("username");

    if (token && username) {
        try {
            await initGlobalChatKey();
            showChat();
            loadMessages(currentChatName);
            connectWS(currentChatName);
        } catch (e) {
            console.error("E2EE init failed on restore:", e);
            logout();
        }
    }
});
