#!/usr/bin/env python3
"""María Mar IA — Servidor de la landing page (Python)"""
import json, os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    import anthropic
except ImportError:
    print("\n❌  Falta instalar el SDK. Ejecuta primero:\n")
    print("    pip3 install anthropic\n")
    sys.exit(1)

MARIA_SYSTEM = """
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
- Eres proactiva: no solo respondes, propones soluciones concretas
- Personalizas tu respuesta según el tipo de empresa/industria del usuario
- Usas ejemplos concretos y situaciones reales cuando explicas algo
- Emojis con moderación, solo cuando añaden claridad

## Contexto del producto
- María Mar IA vive en WhatsApp (el supervisor le escribe directamente)
- Integración nativa con la plataforma Michamba
- Funciona en zonas con conectividad limitada (WhatsApp opera con 2G)
- No requiere capacitación del equipo de campo
- Aprende de la operación de la empresa con el tiempo

## Tu objetivo en esta landing page
1. Demostrar concretamente qué puedes hacer por la empresa del visitante
2. Ser útil y específica según el tipo de empresa/industria que mencionan
3. Responder preguntas sobre el producto de forma clara y honesta
4. Motivarlos a solicitar acceso anticipado al final de la conversación
5. NO inventes precios específicos ni fechas exactas

## Formato de respuestas
- Ultra-concisas: máximo 2 párrafos cortos, 3 oraciones cada uno
- Si el usuario describe su empresa, dale un ejemplo concreto de cómo María les ayudaría
- Ve directo al punto, sin introducciones largas

## Nota importante
Ya enviaste un mensaje de bienvenida al usuario. No vuelvas a presentarte — responde directamente su pregunta.
"""

# Cambiar al directorio del script para servir archivos estáticos
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.send_response(302)
            self.send_header('Location', '/maria-mar-ia.html')
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/chat':
            self._chat()
        else:
            self.send_error(404)

    def _chat(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length))
        messages = body.get('messages', [])[-20:]

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        client = anthropic.Anthropic()
        try:
            with client.messages.stream(
                model='claude-opus-4-6',
                max_tokens=350,
                system=MARIA_SYSTEM,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    payload = json.dumps({'text': text})
                    self.wfile.write(f'data: {payload}\n\n'.encode())
                    self.wfile.flush()
        except Exception as e:
            payload = json.dumps({'error': str(e)})
            self.wfile.write(f'data: {payload}\n\n'.encode())

        self.wfile.write(b'data: [DONE]\n\n')
        self.wfile.flush()

    def log_message(self, fmt, *args):
        pass  # silenciar logs por defecto

PORT = int(os.environ.get('PORT', 3000))

if __name__ == '__main__':
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    print(f'\n✅  Servidor corriendo → http://localhost:{PORT}/maria-mar-ia.html')
    if not api_key:
        print('\n⚠️  Falta la API key. Detén el servidor (Ctrl+C) y ejecuta:')
        print('    ANTHROPIC_API_KEY=sk-ant-... python3 server.py\n')
    else:
        print('    API key: detectada ✓\n')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
