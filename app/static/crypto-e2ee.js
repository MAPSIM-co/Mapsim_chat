// app/static/crypto-e2ee.js

const sodium = window.sodium;
let GLOBAL_KEY = null;

// ================= utils =================
function b64(buf) {
    return sodium.to_base64(buf);
}
function ub64(str) {
    return sodium.from_base64(str);
}


// ================= init global key =================
export async function initGlobalChatKeyFromServer() {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found in localStorage");

    const res = await fetch("/chat/key", {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!res.ok) {
        throw new Error("Failed to fetch global chat key: " + res.status);
    }

    const data = await res.json();

    if (!data.key) throw new Error("No key received from server");

    // ⚡ strip any whitespace or newline
    const keyStr = data.key.trim();
    GLOBAL_KEY = sodium.from_base64(keyStr);

    // ⚡ برای دسترسی در console (فقط تست)
    window.GLOBAL_KEY = GLOBAL_KEY;
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

    //console.log("[E2EE] decrypt called with:", payload);

    if (!GLOBAL_KEY) {
        //console.warn("[E2EE] no global key");
        return "(رمز گشایی نشد)";
    }

    try {
        const { n, c } = JSON.parse(payload);

        const plain = sodium.crypto_secretbox_open_easy(
            ub64(c),
            ub64(n),
            GLOBAL_KEY
        );

        //console.log("[E2EE] decrypt success");
        return sodium.to_string(plain);
    } catch (e) {
        //console.error("decrypt failed:", e);
        return "(رمزنگشایی نشد)";
    }
}
