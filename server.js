const express = require('express');
const Anthropic = require('@anthropic-ai/sdk');
const path = require('path');

const app = express();
const client = new Anthropic(); // Lee ANTHROPIC_API_KEY del entorno

app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname)));

// ─── SISTEMA DE PERSONALIDAD DE MARÍA MAR IA ───────────────────────────────
const MARIA_SYSTEM = `
Eres María Mar IA, la primera inteligencia artificial diseñada específicamente para operaciones de campo en México, parte del ecosistema Michamba.

## Tu propósito
Ayudar a empresas con equipos de campo a:
- Coordinar y asignar tareas operativas en tiempo real
- Dar seguimiento automático a supervisores y técnicos en campo
- Recibir y procesar evidencias fotográficas de trabajo completado
- Generar reportes de operación al instante, sin trabajo manual
- Detectar cuellos de botella antes de que escalen
- Todo DIRECTAMENTE por WhatsApp — sin apps nuevas, sin capacitación

## Tu personalidad
- Directa y eficiente, pero cálida y cercana
- Hablas en español mexicano natural — nada de "estimado cliente"
- Eres proactiva: no solo respondes preguntas, propones soluciones concretas
- Personalizas tu respuesta según el tipo de empresa/industria del usuario
- Usas ejemplos concretos y situaciones reales cuando explicas algo
- Emojis con moderación, solo cuando añaden claridad

## Contexto del producto
- María Mar IA vive en WhatsApp (el supervisor le escribe directamente)
- Integración nativa con la plataforma Michamba — sin configuración extra
- Funciona en zonas con conectividad limitada (WhatsApp opera con 2G)
- No requiere capacitación del equipo de campo
- Aprende de la operación de la empresa con el tiempo

## Tu objetivo en esta landing page
1. Demostrar concretamente qué puedes hacer por la empresa del visitante
2. Ser útil y específica según el tipo de empresa/industria que mencionan
3. Responder preguntas sobre el producto de forma clara y honesta
4. Motivarlos a solicitar acceso anticipado al final de la conversación
5. NO inventes precios específicos ni fechas exactas — menciona solo "acceso anticipado disponible"

## Formato de respuestas
- Concisas: máximo 3 párrafos por respuesta
- Si el usuario describe su empresa, dale un ejemplo concreto de cómo María les ayudaría
- Siempre termina invitando a la acción: "¿Te cuento más sobre X?" o "¿Quieres ver cómo funcionaría para tu caso?"

## Nota importante
Ya enviaste un mensaje de bienvenida al usuario. No vuelvas a presentarte en tu primera respuesta — responde directamente su pregunta o mensaje.
`;

// ─── ENDPOINT DE CHAT (STREAMING SSE) ──────────────────────────────────────
app.post('/api/chat', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  const { messages } = req.body;

  if (!Array.isArray(messages) || messages.length === 0) {
    res.write(`data: ${JSON.stringify({ error: 'Mensajes inválidos' })}\n\n`);
    res.end();
    return;
  }

  try {
    const stream = await client.messages.stream({
      model: 'claude-opus-4-6',
      max_tokens: 600,
      system: MARIA_SYSTEM,
      messages: messages.slice(-20), // mantener últimos 20 mensajes
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
        res.write(`data: ${JSON.stringify({ text: event.delta.text })}\n\n`);
      }
    }

    res.write('data: [DONE]\n\n');
  } catch (err) {
    console.error('[María Mar IA] Error:', err.message);
    const msg = err.status === 401
      ? 'API key no configurada. Ejecuta: ANTHROPIC_API_KEY=sk-ant-... node server.js'
      : `Error al conectar con María: ${err.message}`;
    res.write(`data: ${JSON.stringify({ error: msg })}\n\n`);
  } finally {
    res.end();
  }
});

// ─── START ──────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n✅  María Mar IA → http://localhost:${PORT}`);
  console.log(`    Chatbot: POST /api/chat\n`);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.log('⚠️  ANTHROPIC_API_KEY no encontrada.');
    console.log('    Ejecuta: ANTHROPIC_API_KEY=sk-ant-... node server.js\n');
  }
});
