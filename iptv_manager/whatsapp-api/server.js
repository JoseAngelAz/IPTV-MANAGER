const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
});

let ready = false;

client.on('qr', (qr) => {
    console.log('\n=== ESCANEA ESTE QR CON WHATSAPP EN TU CELULAR ===');
    qrcode.generate(qr, { small: true });
    console.log('==================================================\n');
});

client.on('ready', () => {
    ready = true;
    console.log('[WhatsApp] Cliente conectado y listo');
});

client.on('disconnected', (reason) => {
    ready = false;
    console.log('[WhatsApp] Desconectado:', reason);
});

client.initialize().catch((err) => {
    console.error('[WhatsApp] Error al inicializar:', err);
});

app.get('/health', (_req, res) => {
    res.json({ status: ready ? 'ready' : 'connecting', ready });
});

app.post('/api/send', async (req, res) => {
    const { number, message } = req.body;

    if (!number || !message) {
        return res.status(400).json({ error: 'Faltan campos: number, message' });
    }

    if (!ready) {
        return res.status(503).json({ error: 'WhatsApp no está conectado. Escanea el QR primero.' });
    }

    const chatId = number.includes('@c.us') ? number : `${number}@c.us`;

    try {
        const result = await client.sendMessage(chatId, message);
        console.log(`[WhatsApp] Enviado a ${number}: ${message.substring(0, 40)}...`);
        res.json({ success: true, id: result.id._serialized });
    } catch (err) {
        console.error(`[WhatsApp] Error al enviar a ${number}:`, err.message);
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`[WhatsApp API] Servidor corriendo en http://localhost:${PORT}`);
    console.log(`[WhatsApp API] Endpoint: POST /api/send`);
    console.log(`[WhatsApp API] Health:    GET /health`);
});
