// app/static/chat.js
import { encryptMessage, decryptMessage, initGlobalChatKey } from "./crypto-e2ee.js";


let ws;
let username = null;
let token = null;

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


    // 🌐 بعدش برو سراغ شبکه
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

    // 🔐 init E2EE key
    await initGlobalChatKey();


    showChat();
    connectWS();
}


// ================= Show Chat =================
function showChat() {
    loginSection(false);
    registerSection(false);
    document.getElementById("chat-section").style.display = "block";
    document.getElementById("chat-user").textContent = username;

    loadMessages();
}

// ================= Logout =================
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    token = null;
    username = null;

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

    document.getElementById("login-username").value = "";
    document.getElementById("login-password").value = "";
}

// ================= Load Messages =================
async function loadMessages() {
    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML = "";

    try {
        const res = await fetch("/messages/", {
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
function connectWS() {
    if (!token) {
        console.warn("No token found. WS not connected.");
        return;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(); // اگر WS قبلا باز بود، ببند و reconnect
    }

    const wsProto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${wsProto}://${location.host}/ws?token=${token}`);

    ws.onmessage = e => displayMessage(JSON.parse(e.data));

    ws.onclose = () => {
        console.warn("WebSocket closed.");
        if (token) {
            alert("ارتباط قطع شد. لطفاً دوباره وارد شوید.");
            logout();
        }
    };
}

// ================= Send Message =================
async function sendMessage() {
    const input = document.getElementById("message-input");
    const fileInput = document.getElementById("file-input");

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("اتصال WebSocket برقرار نیست. لطفاً دوباره وارد شوید.");
        return;
    }

    // فایل
    if (fileInput.files.length) {
        const fd = new FormData();
        fd.append("file", fileInput.files[0]);
        const res = await fetch("/upload/", { method: "POST", body: fd });
        const data = await res.json();
        ws.send(JSON.stringify({ type: "file", text: data.file_url }));
        fileInput.value = "";
    }

    // متن
    if (input.value.trim()) {
        try {
            const cipher = await encryptMessage(input.value);
            ws.send(JSON.stringify({ type: "text", text: cipher }));
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

    // ========= FILE =========
    if (msg.type === "file") {
        let body = "";

        const url = msg.text;

        if (/\.(jpg|jpeg|png|gif|heic|jfif)$/i.test(url)) {
            body = `<img src="${url}" class="chat-image">`;
        } else if (/\.(mp4|mov|webm|ogg)$/i.test(url)) {
            body = `
                <video class="chat-video" controls playsinline>
                    <source src="${url}">
                </video>
            `;
        } else if (/\.pdf$/i.test(url)) {
            body = `
                <div class="pdf-box">
                    📄 <a href="${url}" target="_blank">View PDF</a>
                </div>
            `;
        } else {
            body = `<a href="${url}" target="_blank">Download file</a>`;
        }

        wrap.innerHTML = `
            <div class="sender">${msg.username}</div>
            <div class="bubble">${body}</div>
            <div class="time">${formatTime(msg.timestamp)}</div>
        `;

        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;
        return;
    }

    // ========= TEXT =========
    wrap.innerHTML = `
        <div class="sender">${msg.username}</div>
        <div class="bubble">
            <div class="text-message">(در حال بارگذاری…)</div>
        </div>
        <div class="time">${formatTime(msg.timestamp)}</div>
    `;

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;

    decryptMessage(msg.text)
        .then(plain => {
            wrap.querySelector(".bubble").innerHTML =
                `<div class="text-message">${plain}</div>`;
        })
        .catch(() => {
            wrap.querySelector(".bubble").innerHTML =
                `<div class="text-message">(رمزنگشایی نشد)</div>`;
        });
}

function formatTime(ts) {
    return ts
        ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : "";
}


// ================= iOS keyboard fix =================
window.visualViewport?.addEventListener("resize", () => {
    document.body.style.height = window.visualViewport.height + "px";
});
function setRealViewportHeight() {
    const vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.documentElement.style.setProperty('--real-vh', `${vh}px`);
}
setRealViewportHeight();
window.addEventListener('resize', setRealViewportHeight);
window.visualViewport?.addEventListener('resize', setRealViewportHeight);

// ================= Expose to HTML =================
window.login = login;
window.register = register;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.logout = logout;
window.sendMessage = sendMessage;

// ================= Restore session =================
document.addEventListener("DOMContentLoaded", async () => {
    token = localStorage.getItem("token");
    username = localStorage.getItem("username");

    if (token && username) {
        try {
            await initGlobalChatKey(); // 🔐 خیلی مهم
            console.log("[CHAT] Global key restored");
            showChat();
            loadMessages();
            connectWS();
        } catch (e) {
            console.error("E2EE init failed on restore:", e);
            logout();
        }
    }
});

