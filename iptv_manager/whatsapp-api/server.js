const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const qrcodeTerminal = require('qrcode-terminal');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

let qrCodeBase64 = null;
let clientStatus = 'disconnected';

const client = new Client({
    authStrategy: new LocalAuth(),
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
});

client.initialize().catch((err) => {
    console.error('[WhatsApp] Error al inicializar:', err.message);
});

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
        await client.logout();
        await client.destroy();
        qrCodeBase64 = null;
        clientStatus = 'disconnected';
        res.json({ success: true });
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
            result = await client.sendMessage(chatId, mediaFile, { caption: message || '' });
            console.log(`[WhatsApp] Enviado con media a ${number}: ${(message || '').substring(0, 40)}...`);
        } else {
            result = await client.sendMessage(chatId, message);
            console.log(`[WhatsApp] Enviado a ${number}: ${message.substring(0, 40)}...`);
        }
        res.json({ success: true, id: result.id._serialized });
    } catch (err) {
        console.error(`[WhatsApp] Error al enviar a ${number}:`, err.message);
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`[WhatsApp API] Servidor corriendo en http://localhost:${PORT}`);
    console.log(`[WhatsApp API] Endpoints:`);
    console.log(`[WhatsApp API]   POST /api/send`);
    console.log(`[WhatsApp API]   GET  /api/qr`);
    console.log(`[WhatsApp API]   GET  /api/status`);
    console.log(`[WhatsApp API]   POST /api/logout`);
    console.log(`[WhatsApp API]   GET  /health`);
});
