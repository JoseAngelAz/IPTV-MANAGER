const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const qrcodeTerminal = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const DATA_PATH = path.join(__dirname, '.wwebjs_auth');

let qrCodeBase64 = null;
let clientStatus = 'disconnected';
let currentClient = null;

function cleanChromeLocks(dir) {
    const target = dir || DATA_PATH;
    if (!fs.existsSync(target)) {
        console.log(`[WhatsApp] Directorio no existe, creando: ${target}`);
        fs.mkdirSync(target, { recursive: true });
        return;
    }
    let found = 0;
    const items = fs.readdirSync(target);
    for (const item of items) {
        const full = path.join(target, item);
        try {
            if (fs.statSync(full).isDirectory()) {
                cleanChromeLocks(full);
            } else if (item.startsWith('Singleton')) {
                fs.unlinkSync(full);
                console.log(`[WhatsApp] Lock eliminado: ${full}`);
                found++;
            }
        } catch (_) {}
    }
    if (found > 0) {
        console.log(`[WhatsApp] ${found} lock(s) eliminado(s) en ${target}`);
    }
}

function initClient() {
    if (currentClient) {
        try { currentClient.destroy(); } catch (_) {}
        currentClient = null;
    }
    cleanChromeLocks();
    qrCodeBase64 = null;
    clientStatus = 'disconnected';

    const client = new Client({
        authStrategy: new LocalAuth({ dataPath: DATA_PATH }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        },
    });

    client.on('qr', async (qr) => {
        try {
            qrCodeBase64 = await qrcode.toDataURL(qr);
        } catch (err) {
            console.error('[WhatsApp] QR image generation error:', err.message);
        }
        clientStatus = 'connecting';
        console.log('\n=== ESCANEA ESTE QR CON WHATSAPP EN TU CELULAR ===');
        qrcodeTerminal.generate(qr, { small: true });
        console.log('==================================================\n');
    });

    client.on('ready', () => {
        qrCodeBase64 = null;
        clientStatus = 'connected';
        console.log('[WhatsApp] Cliente conectado y listo');
    });

    client.on('disconnected', (reason) => {
        qrCodeBase64 = null;
        clientStatus = 'disconnected';
        console.log('[WhatsApp] Desconectado:', reason);
        if (reason !== 'logout') {
            console.log('[WhatsApp] Reintentando conexión en 5s...');
            setTimeout(initClient, 5000);
        }
    });

    client.on('auth_failure', (msg) => {
        console.error('[WhatsApp] Fallo de autenticación:', msg);
        clientStatus = 'disconnected';
    });

    currentClient = client;
    client.initialize().catch((err) => {
        console.error('[WhatsApp] Error al inicializar:', err.message);
        if (err.message && err.message.includes('Code: 21')) {
            console.log('[WhatsApp] Perfil bloqueado — borrando sesión corrupta y reintentando...');
            const sessionPath = path.join(DATA_PATH, 'session');
            if (fs.existsSync(sessionPath)) {
                fs.rmSync(sessionPath, { recursive: true, force: true });
                console.log('[WhatsApp] Sesión eliminada');
            }
        }
        console.log('[WhatsApp] Reintentando en 10s...');
        setTimeout(initClient, 10000);
    });
}

function getClient() {
    if (currentClient) return currentClient;
    throw new Error('Cliente no inicializado');
}

app.get('/health', (_req, res) => {
    res.json({ status: clientStatus, ready: clientStatus === 'connected' });
});

app.get('/api/qr', (_req, res) => {
    res.json({ qr: qrCodeBase64, status: clientStatus });
});

app.get('/api/status', (_req, res) => {
    res.json({ status: clientStatus, ready: clientStatus === 'connected' });
});

app.post('/api/logout', async (_req, res) => {
    try {
        if (currentClient) {
            await currentClient.logout();
            await currentClient.destroy();
        }
        qrCodeBase64 = null;
        clientStatus = 'disconnected';
        res.json({ success: true });
        console.log('[WhatsApp] Sesión cerrada. Iniciando nueva sesión para QR...');
        initClient();
    } catch (err) {
        console.error('[WhatsApp] Error al cerrar sesión:', err.message);
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/reconnect', async (_req, res) => {
    try {
        if (currentClient) {
            try { await currentClient.destroy(); } catch (_) {}
            currentClient = null;
        }
        const sessionPath = path.join(DATA_PATH, 'session');
        if (fs.existsSync(sessionPath)) {
            fs.rmSync(sessionPath, { recursive: true, force: true });
            console.log('[WhatsApp] Carpeta de sesión eliminada');
        }
        cleanChromeLocks();
        initClient();
        res.json({ success: true, message: 'Reconectando... Escanea el nuevo QR.' });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/send', async (req, res) => {
    const { number, message, media } = req.body;

    if (!number || (!message && !media)) {
        return res.status(400).json({ error: 'Faltan campos: number, y message o media' });
    }

    if (clientStatus !== 'connected') {
        return res.status(503).json({ error: 'WhatsApp no está conectado. Escanea el QR primero.' });
    }

    const chatId = number.includes('@c.us') ? number : `${number}@c.us`;

    try {
        let result;
        if (media && media.url) {
            const mediaFile = await MessageMedia.fromUrl(media.url, { unsafeMime: true });
            result = await currentClient.sendMessage(chatId, mediaFile, { caption: message || '' });
            console.log(`[WhatsApp] Enviado con media a ${number}: ${(message || '').substring(0, 40)}...`);
        } else {
            result = await currentClient.sendMessage(chatId, message);
            console.log(`[WhatsApp] Enviado a ${number}: ${message.substring(0, 40)}...`);
        }
        res.json({ success: true, id: result.id._serialized });
    } catch (err) {
        console.error(`[WhatsApp] Error al enviar a ${number}:`, err.message);
        res.status(500).json({ error: err.message });
    }
});

initClient();

app.listen(PORT, () => {
    console.log(`[WhatsApp API] Servidor corriendo en http://localhost:${PORT}`);
    console.log(`[WhatsApp API] Endpoints:`);
    console.log(`[WhatsApp API]   POST /api/send`);
    console.log(`[WhatsApp API]   GET  /api/qr`);
    console.log(`[WhatsApp API]   GET  /api/status`);
    console.log(`[WhatsApp API]   POST /api/logout`);
    console.log(`[WhatsApp API]   POST /api/reconnect`);
    console.log(`[WhatsApp API]   GET  /health`);
});
