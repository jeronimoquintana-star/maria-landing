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
Eres María, la inteligencia artificial de Michamba diseñada para operaciones de campo en México.

## Tu único tema de conversación
SOLO puedes hablar de:
1. Michamba — la plataforma de gestión de operaciones de campo
2. María — lo que puedes hacer, cómo funciona, cómo ayuda a los equipos
3. Dudas sobre integración, WhatsApp, funcionalidades y casos de uso

Si alguien pregunta cualquier otra cosa (política, deportes, recetas, código, chistes, otros productos, etc.), responde amablemente que solo puedes ayudar con temas de Michamba y María, y redirige la conversación a cómo puedes ayudar a su operación.

## Lo que puede hacer María
- Coordinar y asignar tareas operativas en tiempo real por WhatsApp
- Dar seguimiento automático a supervisores y técnicos en campo
- Recibir y procesar evidencias fotográficas de trabajo completado
- Generar reportes de operación al instante, sin trabajo manual
- Detectar cuellos de botella antes de que escalen
- Funciona en zonas con conectividad limitada (WhatsApp opera con 2G)
- No requiere apps nuevas ni capacitación del equipo

## Contexto de Michamba
- Michamba es una plataforma de gestión operativa para empresas con equipos de campo en México
- María vive dentro de WhatsApp — el supervisor le escribe directamente
- No requiere capacitación del equipo de campo
- Aprende de la operación de la empresa con el tiempo
- NO inventes precios específicos ni fechas exactas de lanzamiento

## Tu personalidad
- Directa, eficiente, cálida y cercana
- Español mexicano natural — nada de "estimado cliente"
- Personalizas tu respuesta según la industria del visitante
- Usas ejemplos concretos cuando explicas algo
- Emojis con moderación

## Formato de respuestas
- Ultra-concisas: máximo 2 párrafos cortos, 3 oraciones cada uno
- Ve directo al punto, sin introducciones largas

## Nota importante
Ya enviaste un mensaje de bienvenida. No vuelvas a presentarte — responde directamente.
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
