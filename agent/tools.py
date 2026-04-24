# agent/tools.py — Notificaciones y Google Sheets
import os
import logging
import httpx

logger = logging.getLogger("agentkit")

OWNER_PHONES = ["5215657176720", "5215591971868"]  # Jose Ramon, Juan Carlos
WHAPI_TOKEN = None


def _get_token():
    global WHAPI_TOKEN
    if not WHAPI_TOKEN:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
    return WHAPI_TOKEN


async def notificar_lead(nombre: str, telefono: str, productos: str, resumen: str):
    """Envía WhatsApp al dueño y registra en Google Sheets."""
    for phone in OWNER_PHONES:
        await _whatsapp_al_dueno(phone, nombre, telefono, productos, resumen)
    sheets_url = os.getenv("GOOGLE_SHEETS_WEBHOOK")
    if sheets_url:
        await _guardar_en_sheets(sheets_url, nombre, telefono, productos, resumen)


async def _whatsapp_al_dueno(destinatario: str, nombre: str, telefono: str, productos: str, resumen: str):
    token = _get_token()
    if not token:
        logger.warning("WHAPI_TOKEN no configurado")
        return
    mensaje = (
        f"🔔 *Nuevo lead — As Molinas*\n\n"
        f"👤 *Nombre:* {nombre}\n"
        f"📞 *Teléfono:* {telefono}\n"
        f"🛒 *Interés:* {productos}\n\n"
        f"📝 *Resumen:*\n{resumen}"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://gate.whapi.cloud/messages/text",
                json={"to": destinatario, "body": mensaje},
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                logger.info(f"Notificación enviada al dueño: {nombre} / {telefono}")
            else:
                logger.error(f"Error enviando notificación a {destinatario}: {r.status_code} {r.text}")
    except Exception as e:
        logger.error(f"Error en notificación WhatsApp: {e}")


async def _guardar_en_sheets(webhook_url: str, nombre: str, telefono: str, productos: str, resumen: str):
    from datetime import datetime
    datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "nombre": nombre,
        "telefono": telefono,
        "productos": productos,
        "resumen": resumen,
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(webhook_url, json=datos, timeout=10)
            if r.status_code == 200:
                logger.info(f"Lead guardado en Sheets: {nombre}")
            else:
                logger.error(f"Error en Sheets: {r.status_code}")
    except Exception as e:
        logger.error(f"Error guardando en Sheets: {e}")
