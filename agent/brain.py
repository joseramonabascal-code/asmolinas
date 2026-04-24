# agent/brain.py — Cerebro del agente: conexión con Claude API
import os
import yaml
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("agentkit")

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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
