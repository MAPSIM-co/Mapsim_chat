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
export async function initGlobalChatKey() {
    await sodium.ready;
    //console.log("[E2EE] sodium ready");

    // 🔐 secret مشترک برای همه device ها
    const GLOBAL_SECRET = "MADOL_GLOBAL_CHAT_v1";

    GLOBAL_KEY = sodium.crypto_generichash(
        32,
        sodium.from_string(GLOBAL_SECRET)
    );

    //console.log("[E2EE] global key derived, length:", GLOBAL_KEY.length);
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
        console.warn("[E2EE] no global key");
        return "(رمزنگشایی نشد)";
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
        console.error("[E2EE] decrypt failed:", e);
        return "(رمزنگشایی نشد)";
    }
}
