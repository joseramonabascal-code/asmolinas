import os
import yaml
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("telegram_bot")

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT_INTERNO = """Eres el asistente interno de As Molinas, una empresa de compra y venta de semillas, especias, frutos secos y superfoods que atiende a hoteles, restaurantes y clientes particulares.

## Tu rol
Eres el asistente de confianza del equipo interno — no de los clientes. Ayudas a los dueños y empleados a gestionar el negocio.

## Lo que puedes hacer
- Redactar contenido: posts para redes sociales, emails, respuestas a clientes, propuestas comerciales
- Responder preguntas sobre el negocio, productos, precios y políticas
- Analizar y resumir conversaciones con clientes de WhatsApp
- Ayudar con tareas generales: cálculos, listas, comparaciones, estrategias
- Generar plantillas de respuestas para situaciones frecuentes
- Dar recomendaciones de ventas y marketing para el sector de alimentos

## Tono
- Directo y eficiente — el equipo interno no necesita formalidades
- Proporciona información concisa y útil
- Si te piden contenido para clientes, adapta el tono a "amigable y profesional"

## Contexto del negocio
- Nombre: As Molinas
- Sector: Semillas, especias, frutos secos y superfoods
- Clientes: Hoteles, restaurantes y particulares
- Horario: Lunes a Viernes 9:00 AM - 7:00 PM
- Agente de WhatsApp para clientes: Moli

Responde siempre en español."""


async def responder(mensaje: str, historial: list[dict]) -> str:
    if not mensaje or len(mensaje.strip()) < 2:
        return "No entendí tu mensaje. ¿Puedes repetirlo?"

    mensajes = [{"role": m["role"], "content": m["content"]} for m in historial]
    mensajes.append({"role": "user", "content": mensaje})

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT_INTERNO,
            messages=mensajes
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error Claude API: {e}")
        return "Hubo un error al conectar con Claude. Intenta de nuevo."


async def resumir_conversacion(historial_cliente: list[dict], numero: str) -> str:
    if not historial_cliente:
        return f"No hay conversación registrada para el número {numero}."

    conversacion = "\n".join(
        f"{'Cliente' if m['role'] == 'user' else 'Moli'}: {m['content']}"
        for m in historial_cliente
    )

    prompt = f"""Resume esta conversación de WhatsApp del cliente {numero} con As Molinas.

Incluye:
- Qué quería o preguntó el cliente
- Qué productos le interesaron (si aplica)
- Si hizo un pedido (cantidad, productos, precio si se mencionó)
- Estado de la conversación (cerrada, pendiente, requiere seguimiento)
- Datos de contacto del cliente si los compartió

Conversación:
{conversacion}"""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="Eres un asistente interno de As Molinas. Haz resúmenes claros y accionables.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error resumiendo conversación: {e}")
        return "Error al generar el resumen. Intenta de nuevo."
