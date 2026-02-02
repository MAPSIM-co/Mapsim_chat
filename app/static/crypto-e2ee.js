// app/static/crypto-e2ee.js

const DEBUG = true; // جهت فعالسازی دیباگ کنسول

const sodium = window.sodium;
let GLOBAL_KEY = null;

// ================= utils =================
function b64(buf) {
    return sodium.to_base64(buf);
}
function ub64(str) {
    return sodium.from_base64(str);
}


export function __reset() {
    GLOBAL_KEY = null;
    delete window.GLOBAL_KEY;
}
// ================= init global key =================
export async function initGlobalChatKeyFromServer() {
    await sodium.ready;

    // 1️⃣ اگر قبلاً در RAM داریم
    if (GLOBAL_KEY) return GLOBAL_KEY;

    // 2️⃣ اگر در sessionStorage هست
    const cached = sessionStorage.getItem("GLOBAL_CHAT_KEY");
    if (cached) {
        GLOBAL_KEY = sodium.from_base64(cached);
        window.GLOBAL_KEY = GLOBAL_KEY; // فقط تست
        return GLOBAL_KEY;
    }

    // 3️⃣ گرفتن از سرور
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const res = await fetch("/chat/key", {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!res.ok) {
        throw new Error("Failed to fetch global chat key: " + res.status);
    }

    const data = await res.json();
    if (!data.key) throw new Error("No key received from server");

    const keyStr = data.key.trim();

    GLOBAL_KEY = sodium.from_base64(keyStr);

    // 4️⃣ ذخیره در sessionStorage
    sessionStorage.setItem("GLOBAL_CHAT_KEY", keyStr);

    // فقط برای debug
    if (DEBUG) {
        window.GLOBAL_KEY = GLOBAL_KEY;
    }

    return GLOBAL_KEY;
}


// ================= encrypt =================
export async function encryptMessage(text) {
    await sodium.ready;
    if (!GLOBAL_KEY) throw "Global key not initialized";

    const nonce = sodium.randombytes_buf(
        sodium.crypto_secretbox_NONCEBYTES
    );

    const cipher = sodium.crypto_secretbox_easy(
        sodium.from_string(text),
        nonce,
        GLOBAL_KEY
    );

    //console.log("[E2EE] encrypt called");


    // JSON امن‌تر از split(":")
    return JSON.stringify({
        n: b64(nonce),
        c: b64(cipher)
    });
}

// ================= decrypt =================
export async function decryptMessage(payload) {
    await sodium.ready;

    // ⬅️ این خط کل مشکل را حل می‌کند
    await initGlobalChatKeyFromServer();

    try {
        const { n, c } = JSON.parse(payload);

        const plain = sodium.crypto_secretbox_open_easy(
            ub64(c),
            ub64(n),
            GLOBAL_KEY
        );

        return sodium.to_string(plain);
    } catch (e) {
        return "(رمزگشایی نشد)";
    }
}