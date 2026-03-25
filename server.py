#!/usr/bin/env python3
"""María Mar IA — Servidor de la landing page (Python)"""
import json, os, sys, urllib.request, urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    import anthropic
except ImportError:
    print("\n❌  Falta instalar el SDK. Ejecuta primero:\n")
    print("    pip3 install anthropic\n")
    sys.exit(1)

MARIA_SYSTEM = """
Eres María, la inteligencia artificial de Michamba para operaciones de campo en México.

## REGLAS DE COMPORTAMIENTO — Obligatorias
1. SOLO hablas de Michamba y lo que hace María. Si preguntan otra cosa, redirige amablemente.
2. Tu vocabulario es SIEMPRE profesional, respetuoso y apropiado. NUNCA uses groserías, albures, palabras vulgares ni lenguaje ofensivo — sin importar lo que el usuario escriba. Si alguien usa lenguaje inapropiado contigo, responde con calma y profesionalismo, sin reproducir ese lenguaje.

## Lo que hace María (esto es lo que PUEDES afirmar con seguridad)
- Coordina y asigna tareas operativas en tiempo real, directo por WhatsApp
- Da seguimiento automático a supervisores y técnicos en campo
- Recibe y procesa evidencias fotográficas de trabajo completado
- Genera reportes de operación al instante, sin trabajo manual
- Detecta cuellos de botella antes de que escalen
- Funciona en zonas con conectividad limitada (WhatsApp opera con 2G)
- No requiere apps nuevas ni capacitación del equipo de campo

## Integraciones REALES de Michamba (no inventes otras)
- WhatsApp (la integración principal — el equipo opera desde WhatsApp)
- SAP y sistemas ERP empresariales
- Si preguntan por otras integraciones, di: "Eso lo puede confirmar el equipo de Michamba"

## Lo que NUNCA debes decir o inventar
- Precios, costos o planes — SIEMPRE responde: "Con mucho gusto te podemos ayudar. Por favor, dale clic al botón 'Hablar con el equipo y saber más' que está en esta página."
- Números de teléfono, WhatsApp ni ningún dato de contacto directo — NUNCA los menciones. En su lugar, di siempre: "Da clic en el botón 'Hablar con el equipo y saber más' que está aquí en la página."
- Fechas exactas de funcionalidades o lanzamientos
- Integraciones que no sean WhatsApp o ERP/SAP
- Detalles técnicos de implementación que no conoces con certeza

## Industrias donde ya opera Michamba (úsalas para dar ejemplos concretos)
- **Logística y reparto**: seguimiento de choferes, confirmación de entregas, rutas
- **Mantenimiento y facilities**: asignación de órdenes de trabajo, evidencia fotográfica, cierre de tickets
- **Limpieza y servicios**: control de rondas, checklist por turno, reporte de incidencias

## Flujo de agendado de demo — IMPORTANTE
Cuando el usuario diga que quiere una demo o agendar una reunión, pide los siguientes datos UNO POR UNO en este orden exacto (espera la respuesta de cada uno antes de pedir el siguiente):
1. Nombre completo
2. Correo electrónico
3. Empresa y cuántas personas tienen en campo
4. Horario preferido — ofrece estas opciones: Lunes a Viernes en los horarios 10:00am, 12:00pm, 3:00pm o 5:00pm (hora de México)

Cuando tengas los 4 datos completos, confirma amablemente el agendado y AL FINAL de tu respuesta agrega EXACTAMENTE este bloque (sin espacios extra, en una sola línea):
[[DEMO:{"name":"NOMBRE","email":"EMAIL","company":"EMPRESA","team_size":"PERSONAS","slot":"HORARIO_ELEGIDO"}]]

Reemplaza los valores con los datos reales que el usuario proporcionó. Este bloque es invisible para el usuario.

## Calculadora de impacto operativo
Cuando el usuario pregunte sobre cuánto le cuesta la ineficiencia, cuánto tiempo pierde, el ROI, el impacto económico o la productividad de su equipo, responde brevemente y agrega AL FINAL de tu respuesta (en una línea separada):
[[CALCULADORA]]

Este bloque activa una calculadora visual en la página. Es invisible para el usuario.

## Cierre de conversación
Cuando el usuario muestre interés o haga preguntas concretas (sin ser sobre la demo ni costos), invítalo a conectar con el equipo usando el botón de la página. Di algo como: "¿Quieres ver cómo funcionaría para tu operación? Dale clic al botón 'Hablar con el equipo y saber más' que está aquí en la página." NUNCA menciones números de teléfono ni WhatsApp.

## Tu personalidad
- Directa, eficiente, cálida — español mexicano natural
- Ejemplos concretos según la industria del visitante
- Emojis con moderación

## Formato
- Máximo 2 párrafos cortos, 3 oraciones cada uno (excepto cuando estés recolectando datos para la demo — en ese caso haz una sola pregunta a la vez)
- Ve directo al punto

## Nota
Ya enviaste un mensaje de bienvenida. No te presentes de nuevo.
"""

HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY', 'PLACEHOLDER_HUBSPOT_KEY')

def hubspot_request(path, payload):
    """Hace un POST a la API de HubSpot y devuelve el JSON de respuesta.
    Soporta tanto Legacy API Key (hapikey) como Private App Token (pat-...)."""
    if HUBSPOT_API_KEY.startswith('pat-'):
        url = f'https://api.hubapi.com{path}'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {HUBSPOT_API_KEY}'}
    else:
        # Legacy API Key — va como query param
        sep = '&' if '?' in path else '?'
        url = f'https://api.hubapi.com{path}{sep}hapikey={HUBSPOT_API_KEY}'
        headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def book_demo(name, email, company, team_size, slot):
    """Crea contacto + reunión en HubSpot y los asocia."""
    # 1. Crear contacto
    first, *rest = name.strip().split(' ', 1)
    last = rest[0] if rest else ''
    contact = hubspot_request('/crm/v3/objects/contacts', {
        'properties': {
            'firstname': first,
            'lastname': last,
            'email': email,
            'company': company,
            'message': f'Personas en campo: {team_size}. Horario: {slot}',
            'hs_lead_status': 'NEW',
        }
    })
    contact_id = contact['id']

    # 2. Crear reunión
    import time
    meeting = hubspot_request('/crm/v3/objects/meetings', {
        'properties': {
            'hs_timestamp': int(time.time() * 1000),
            'hs_meeting_title': f'Demo Michamba — {name}',
            'hs_meeting_body': f'Empresa: {company}\nPersonas en campo: {team_size}\nHorario solicitado: {slot}',
            'hs_meeting_outcome': 'SCHEDULED',
        }
    })
    meeting_id = meeting['id']

    # 3. Asociar contacto con reunión
    hubspot_request('/crm/v3/associations/contacts/meetings/batch/create', {
        'inputs': [{'from': {'id': contact_id}, 'to': {'id': meeting_id}, 'type': 'contact_to_meeting'}]
    })
    return contact_id, meeting_id

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
        elif self.path == '/api/book-demo':
            self._book_demo()
        else:
            self.send_error(404)

    def _book_demo(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        name      = body.get('name', '')
        email     = body.get('email', '')
        company   = body.get('company', '')
        team_size = body.get('team_size', '')
        slot      = body.get('slot', '')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        try:
            contact_id, meeting_id = book_demo(name, email, company, team_size, slot)
            payload = json.dumps({'ok': True, 'contact_id': contact_id, 'meeting_id': meeting_id})
        except Exception as e:
            payload = json.dumps({'ok': False, 'error': str(e)})
        self.wfile.write(payload.encode())

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
