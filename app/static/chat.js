// app/static/chat.js

import * as e2ee from "./crypto-e2ee.js";

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

    // 🌐 login
    let res;
    try {
        res = await fetch("/login/", {
            method: "POST",
            body: new URLSearchParams({ username, password })
        });
    } catch (e) {
        alert("خطا در اتصال به سرور");
        return;
    }

    if (!res.ok) {
        alert("نام کاربری یا رمز عبور اشتباه است");
        return;
    }

    const data = await res.json();
    token = data.access_token;

    localStorage.setItem("token", token);
    localStorage.setItem("username", username);

    // 🔐 بعد از لاگین، کلید global را از سرور می‌گیریم
    try {
        await e2ee.initGlobalChatKeyFromServer(token);  // حتماً token را به سرور بفرست
    } catch (e) {
        console.error("E2EE init failed:", e);
        alert("رمزنگاری فعال نشد.");
        return;
    }

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
    console.log("در حال اتصال به WebSocket، chatName =", chatName); // 🔹 این خط برای دیبا
    if (!token) return;

    if (ws && ws.readyState === WebSocket.OPEN) ws.close();

    const wsProto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${wsProto}://${location.host}/ws?token=${token}&chat_name=${chatName}`);

    ws.onmessage = e => {
        const msg = JSON.parse(e.data);

        if (msg.type === "online_users") {
            console.log("کاربران آنلاین:", msg.users);
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
document.getElementById("sendBtn").addEventListener("click", sendMessage);

async function sendMessage() {
    const input = document.getElementById("message-input");
    const fileInput = document.getElementById("file-input");
    const sendBtn = document.getElementById("sendBtn");
    const btnSpinner = sendBtn.querySelector(".btn-spinner");
    const btnPercent = sendBtn.querySelector(".btn-percent");

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("اتصال WebSocket برقرار نیست.");
        return;
    }

    // 🔹 فایل
    if (fileInput.files.length) {
        sendBtn.disabled = true;
        btnSpinner.style.display = "block";
        btnPercent.style.display = "block";
        btnPercent.textContent = "0%";

        const fd = new FormData();
        fd.append("file", fileInput.files[0]);

        try {
            const res = await axios.post("/upload/", fd, {
                onUploadProgress: progressEvent => {
                    const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    btnPercent.textContent = percent + "%";
                }
            });

            // ارسال پیام فایل
            ws.send(JSON.stringify({
                type: "file",
                text: res.data.file_url,
                chat_name: currentChatName
            }));

        } catch (e) {
            alert("آپلود فایل انجام نشد: " + e);
        } finally {
            sendBtn.disabled = false;
            btnSpinner.style.display = "none";
            btnPercent.style.display = "none";
            fileInput.value = "";
        }
    }

    // 🔹 متن
    if (input.value.trim()) {
        try {
            const cipher = await e2ee.encryptMessage(input.value);
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

        // تصاویر
        if (/\.(jpg|jpeg|png|gif|heic|jfif|bmp|tiff|svg)$/i.test(url)) {
            body = `<img src="${url}" class="chat-image">`;
        }
        // ویدیوها
        else if (/\.(mp4|mov|webm|ogg|avi|mkv|flv|wmv)$/i.test(url)) {
            body = `<video class="chat-video" controls playsinline><source src="${url}"></video>`;
        }
        // صداها
        else if (/\.(mp3|wav|aac|m4a|ogg|flac)$/i.test(url)) {
            body = `<audio controls><source src="${url}"></audio>`;
        }
        // پی‌دی‌اف
        else if (/\.pdf$/i.test(url)) {
            body = `<div class="pdf-box">📄 <a href="${url}" target="_blank">View PDF</a></div>`;
        }
        // آرشیوها
        else if (/\.(zip|rar|7z|tar|gz)$/i.test(url)) {
            body = `<div class="archive-box">📦 <a href="${url}" target="_blank">Download Archive</a></div>`;
        }
        // فایل‌های متنی و دیگر فرمت‌ها
        else {
            body = `<a href="${url}" target="_blank">Download File</a>`;
        }

        wrap.innerHTML = `<div class="sender">${msg.username}</div>
                          <div class="bubble">${body}</div>
                          <div class="time">${formatTime(msg.timestamp)}</div>`;
        messages.appendChild(wrap);
        messages.scrollTop = messages.scrollHeight;
        return;
    }

    // متن
    wrap.innerHTML = `<div class="sender">${msg.username}</div>
                      <div class="bubble"><div class="text-message">(در حال بارگذاری…)</div></div>
                      <div class="time">${formatTime(msg.timestamp)}</div>`;
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;

    e2ee.decryptMessage(msg.text)
        .then(plain => wrap.querySelector(".bubble").innerHTML = `<div class="text-message">${plain}</div>`)
        .catch(() => wrap.querySelector(".bubble").innerHTML = `<div class="text-message">(رمز گشایی نشد)</div>`);
}


// ================= Online Users =================
function renderOnlineUsers() {
    const container = document.getElementById("online-users-container");
    if (!container) return;

    container.innerHTML = onlineUsers
        .filter(u => u !== username)
        .map(u => `<span class="user-item" onclick="startPrivateChat('${u}')">${u}</span>`)
        .join("");
}

// ================= Start Private Chat =================
function startPrivateChat(otherUser) {
    currentChatName = `private_${[username, otherUser].sort().join("_")}`;
    loadMessages(currentChatName);
    connectWS(currentChatName);
}

// ================= Update Online Users =================
function updateOnlineUsers(users) {
    onlineUsers = users;
    renderOnlineUsers();
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



document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("loginBtn").addEventListener("click", login);
    document.getElementById("showRegister").addEventListener("click", showRegister);

    token = localStorage.getItem("token");
    username = localStorage.getItem("username");
    if (token && username) {
        try {
            await e2ee.initGlobalChatKeyFromServer();
            showChat();
            loadMessages(currentChatName);
            connectWS(currentChatName);
        } catch (e) {
            console.error("E2EE init failed on restore:", e);
            logout();
        }
    }
});
