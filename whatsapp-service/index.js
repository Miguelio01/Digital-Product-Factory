const { 
    default: makeWASocket, 
    useMultiFileAuthState, 
    DisconnectReason, 
    fetchLatestBaileysVersion,
    makeCacheableSignalKeyStore
} = require('@whiskeysockets/baileys');
const { Bot } = require('grammy'); // Librería de Telegram
const qrcode = require('qrcode-terminal');
const express = require('express');
const pino = require('pino');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const logger = pino({ level: 'info' });
const app = express();
app.use(express.json());

const AUTH_DIR = path.join(__dirname, 'sessions');
const PYTHON_BACKEND = process.env.PYTHON_BACKEND || 'http://localhost:8000';

let sock; // WhatsApp Socket
let isWaConnected = false;
let tgBot; // Telegram Bot

// --- WHATSAPP ENGINE ---
async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    let { version } = await fetchLatestBaileysVersion().catch(() => ({ version: [2, 3000, 1017531287] }));

    sock = makeWASocket({
        version,
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys, logger.child({ level: 'silent' })),
        },
        printQRInTerminal: false,
        logger: pino({ level: 'silent' }),
        browser: ['Mac OS', 'Chrome', '121.0.6167.139'],
        syncFullHistory: false,
        markOnlineOnConnect: true
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log('\n✨ [ESCANEA PARA WHATSAPP]');
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode || lastDisconnect?.error?.status;
            if (statusCode === DisconnectReason.loggedOut || statusCode === 401) {
                if (fs.existsSync(AUTH_DIR)) fs.readdirSync(AUTH_DIR).forEach(f => fs.rmSync(path.join(AUTH_DIR, f), { recursive: true, force: true }));
            }
            setTimeout(connectToWhatsApp, 5000);
            isWaConnected = false;
        } else if (connection === 'open') {
            console.log('✅ WhatsApp: CONECTADO');
            isWaConnected = true;
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        if (m.type === 'notify') {
            for (const msg of m.messages) {
                if (!msg.key.fromMe && msg.message) {
                    const sender = msg.key.remoteJid;
                    const text = msg.message.conversation || msg.message.extendedTextMessage?.text || "";
                    if (text) {
                        forwardToPython(sender, text, 'whatsapp');
                    }
                }
            }
        }
    });
}

// --- TELEGRAM ENGINE ---
async function connectToTelegram() {
    const token = process.env.TELEGRAM_BOT_TOKEN;
    if (!token) {
        console.log('⚠️ TELEGRAM_BOT_TOKEN no configurado. Telegram desactivado.');
        return;
    }

    tgBot = new Bot(token);

    tgBot.on('message:text', async (ctx) => {
        const sender = ctx.from.id.toString();
        const text = ctx.message.text;
        console.log(`📩 [Telegram] ${sender}: ${text}`);
        forwardToPython(sender, text, 'telegram');
    });

    tgBot.start();
    console.log('✅ Telegram: BOT ACTIVO');
}

// --- SHARED UTILS ---
async function forwardToPython(sender, message, channel) {
    try {
        const fullId = channel === 'whatsapp' ? sender : `tg_${sender}`;
        await fetch(`${PYTHON_BACKEND}/whatsapp/webhook`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: fullId, message: message })
        });
    } catch (err) {
        console.error(`❌ Error reenvío ${channel}:`, err.message);
    }
}

// --- API ENDPOINTS ---
app.post('/send', async (req, res) => {
    const { to, text } = req.body;
    
    // Detectar si es envío para Telegram o WhatsApp
    if (to.startsWith('tg_')) {
        const chatId = to.replace('tg_', '');
        if (!tgBot) return res.status(503).json({ error: 'Telegram bot not active' });
        try {
            await tgBot.api.sendMessage(chatId, text);
            return res.json({ status: 'sent', channel: 'telegram' });
        } catch (err) {
            return res.status(500).json({ error: err.message });
        }
    } else {
        if (!isWaConnected) return res.status(503).json({ error: 'WhatsApp not connected' });
        try {
            const jid = to.includes('@') ? to : `${to}@s.whatsapp.net`;
            await sock.sendMessage(jid, { text });
            return res.json({ status: 'sent', channel: 'whatsapp' });
        } catch (err) {
            return res.status(500).json({ error: err.message });
        }
    }
});

app.listen(8001, () => {
    console.log('🚀 Sidecar Multi-Canal (WA + TG) en puerto 8001');
    connectToWhatsApp();
    connectToTelegram();
});
