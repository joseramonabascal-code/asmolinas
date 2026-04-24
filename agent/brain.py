# agent/brain.py — Cerebro del agente: conexión con Claude API
import os
import re
import json
import yaml
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("agentkit")

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPT_DETECTOR_LEAD = """Analiza esta conversación de WhatsApp entre un cliente y el asistente de As Molinas.

Determina si el cliente proporcionó sus datos de contacto (nombre Y teléfono/email).

Responde SOLO con JSON válido, sin texto adicional:
{
  "lead_capturado": true/false,
  "nombre": "nombre del cliente o null",
  "telefono": "teléfono o null",
  "productos": "productos de interés resumidos o null",
  "resumen": "resumen breve del pedido en 1-2 oraciones o null"
}"""


def cargar_config_prompts() -> dict:
    try:
        with open("config/prompts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/prompts.yaml no encontrado")
        return {}


def cargar_system_prompt() -> str:
    config = cargar_config_prompts()
    return config.get("system_prompt", "Eres Moli, asistente de As Molinas. Responde en español.")


async def generar_respuesta(mensaje: str, historial: list[dict]) -> str:
    config = cargar_config_prompts()
    fallback = config.get("fallback_message", "Disculpa, no entendí. ¿Puedes repetirlo?")
    error_msg = config.get("error_message", "Problema técnico, intenta de nuevo.")

    if not mensaje or len(mensaje.strip()) < 2:
        return fallback

    system_prompt = cargar_system_prompt()
    mensajes = [{"role": m["role"], "content": m["content"]} for m in historial]
    mensajes.append({"role": "user", "content": mensaje})

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=mensajes
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error Claude API: {e}")
        return error_msg


async def detectar_lead(historial: list[dict]) -> dict | None:
    """Detecta si se capturó un lead en la conversación. Retorna datos del lead o None."""
    if len(historial) < 4:
        return None

    # Convertir historial a texto para análisis
    conversacion = "\n".join(
        f"{'Cliente' if m['role'] == 'user' else 'Moli'}: {m['content']}"
        for m in historial[-10:]  # últimos 10 mensajes
    )

    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=PROMPT_DETECTOR_LEAD,
            messages=[{"role": "user", "content": conversacion}]
        )
        texto = response.content[0].text.strip()
        # Extraer JSON
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            datos = json.loads(match.group())
            if datos.get("lead_capturado") and datos.get("nombre") and datos.get("telefono"):
                return datos
    except Exception as e:
        logger.error(f"Error detectando lead: {e}")
    return None
