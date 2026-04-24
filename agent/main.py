# agent/main.py — Servidor FastAPI + Webhook de WhatsApp
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta, detectar_lead
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.providers import obtener_proveedor
from agent.tools import notificar_lead

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
logging.basicConfig(level=logging.DEBUG if ENVIRONMENT == "development" else logging.INFO)
logger = logging.getLogger("agentkit")

proveedor = obtener_proveedor()
PORT = int(os.getenv("PORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_db()
    logger.info(f"Agente Moli (As Molinas) corriendo en puerto {PORT}")
    yield


app = FastAPI(title="Moli — Agente WhatsApp de As Molinas", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "agente": "Moli", "negocio": "As Molinas"}


@app.get("/test-notificacion")
async def test_notificacion():
    """Dispara una notificación de prueba a los dueños para verificar que Whapi funciona."""
    from agent.tools import notificar_lead
    await notificar_lead(
        nombre="Cliente de Prueba",
        telefono="5512345678",
        productos="Prueba del sistema",
        resumen="Este es un mensaje de prueba para verificar que las notificaciones llegan correctamente.",
    )
    return {"status": "notificacion_enviada"}


@app.get("/debug")
async def debug():
    import traceback
    resultado = {}
    try:
        resultado["ANTHROPIC_API_KEY"] = bool(os.getenv("ANTHROPIC_API_KEY"))
        resultado["WHAPI_TOKEN"] = bool(os.getenv("WHAPI_TOKEN"))
        resultado["WHATSAPP_PROVIDER"] = os.getenv("WHATSAPP_PROVIDER")
        resultado["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite default")
        from agent.memory import inicializar_db
        await inicializar_db()
        resultado["db"] = "ok"
        from agent.brain import generar_respuesta
        respuesta = await generar_respuesta("test", [])
        resultado["claude"] = respuesta[:50]
    except Exception as e:
        resultado["error"] = f"{type(e).__name__}: {e}"
        resultado["trace"] = traceback.format_exc()
    return resultado


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        mensajes = await proveedor.parsear_webhook(request)
        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue
            logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")
            historial = await obtener_historial(msg.telefono)
            respuesta = await generar_respuesta(msg.texto, historial)
            await guardar_mensaje(msg.telefono, "user", msg.texto)
            await guardar_mensaje(msg.telefono, "assistant", respuesta)
            await proveedor.enviar_mensaje(msg.telefono, respuesta)
            logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

            # Detectar si se capturó un lead y notificar al dueño
            historial_actualizado = await obtener_historial(msg.telefono)
            lead = await detectar_lead(historial_actualizado)
            if lead:
                logger.info(f"Lead capturado: {lead['nombre']} / {lead['telefono']}")
                await notificar_lead(
                    nombre=lead.get("nombre", ""),
                    telefono=lead.get("telefono", ""),
                    productos=lead.get("productos", ""),
                    resumen=lead.get("resumen", ""),
                )
        return {"status": "ok"}
    except Exception as e:
        import traceback
        logger.error(f"Error en webhook: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
