import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from sqlalchemy import select, func

# Agregar raíz del proyecto al path para importar módulos compartidos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.memory import inicializar_db, obtener_historial, guardar_mensaje, async_session, Mensaje
from telegram_bot.brain import responder, resumir_conversacion

load_dotenv(override=True)

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("telegram_bot")

# IDs de Telegram autorizados (separados por coma en .env)
# Si está vacío, cualquiera puede usar el bot
USUARIOS_AUTORIZADOS = set(
    int(x.strip())
    for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
    if x.strip().isdigit()
)

# Prefijo para historial interno del bot en la BD
PREFIJO_TELEGRAM = "telegram-"


def autorizado(user_id: int) -> bool:
    if not USUARIOS_AUTORIZADOS:
        return True
    return user_id in USUARIOS_AUTORIZADOS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        await update.message.reply_text("No tienes acceso a este bot.")
        return

    await update.message.reply_text(
        "Hola! Soy el asistente interno de *As Molinas* 🌿\n\n"
        "Puedo ayudarte con:\n"
        "• Cualquier pregunta o tarea — escríbeme directamente\n"
        "• `/clientes` — ver últimas conversaciones de WhatsApp\n"
        "• `/resumen NUMERO` — resumir conversación de un cliente\n"
        "• `/limpiar` — borrar nuestro historial de chat\n"
        "• `/ayuda` — ver todos los comandos\n\n"
        "¿En qué te ayudo?",
        parse_mode="Markdown"
    )


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    await update.message.reply_text(
        "*Comandos disponibles:*\n\n"
        "`/clientes` — Lista los últimos clientes que escribieron por WhatsApp\n"
        "`/resumen NUMERO` — Resume la conversación con ese número\n"
        "  Ej: `/resumen 521234567890`\n"
        "`/limpiar` — Borra el historial de esta conversación\n"
        "`/ayuda` — Muestra este mensaje\n\n"
        "*Para cualquier otra tarea*, escríbeme directamente:\n"
        "• _\"Redacta un post de Instagram sobre nuestras especias\"_\n"
        "• _\"¿Cuál es el precio de venta sugerido para almendras?\"_\n"
        "• _\"Crea una respuesta para un cliente que se queja del envío\"_",
        parse_mode="Markdown"
    )


async def cmd_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    await update.message.reply_text("Buscando conversaciones recientes de WhatsApp...")

    try:
        async with async_session() as session:
            # Obtener los últimos 15 números únicos (excluyendo conversaciones internas de Telegram)
            subq = (
                select(
                    Mensaje.telefono,
                    func.max(Mensaje.timestamp).label("ultimo")
                )
                .where(~Mensaje.telefono.startswith(PREFIJO_TELEGRAM))
                .group_by(Mensaje.telefono)
                .order_by(func.max(Mensaje.timestamp).desc())
                .limit(15)
                .subquery()
            )
            result = await session.execute(
                select(subq.c.telefono, subq.c.ultimo)
            )
            filas = result.fetchall()

        if not filas:
            await update.message.reply_text("No hay conversaciones de WhatsApp registradas aún.")
            return

        lineas = ["*Últimas conversaciones de WhatsApp:*\n"]
        for i, (telefono, ultimo) in enumerate(filas, 1):
            hora = ultimo.strftime("%d/%m %H:%M") if isinstance(ultimo, datetime) else str(ultimo)
            lineas.append(f"{i}. `{telefono}` — {hora}")

        lineas.append("\nUsa `/resumen NUMERO` para ver el detalle de una conversación.")
        await update.message.reply_text("\n".join(lineas), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error en /clientes: {e}")
        await update.message.reply_text("Error al consultar la base de datos. ¿Está corriendo el agente de WhatsApp?")


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Indica el número de teléfono.\nEj: `/resumen 521234567890`",
            parse_mode="Markdown"
        )
        return

    numero = context.args[0].strip()
    await update.message.reply_text(f"Generando resumen de la conversación con `{numero}`...", parse_mode="Markdown")

    historial = await obtener_historial(numero, limite=50)
    resumen = await resumir_conversacion(historial, numero)
    await update.message.reply_text(resumen)


async def cmd_limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    user_id = str(update.effective_user.id)
    clave = f"{PREFIJO_TELEGRAM}{user_id}"

    from agent.memory import limpiar_historial
    await limpiar_historial(clave)
    await update.message.reply_text("Historial borrado. Empezamos de cero.")


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        await update.message.reply_text("No tienes acceso a este bot.")
        return

    user_id = str(update.effective_user.id)
    clave = f"{PREFIJO_TELEGRAM}{user_id}"
    texto = update.message.text

    # Indicador de escritura mientras Claude piensa
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    historial = await obtener_historial(clave, limite=20)
    respuesta = await responder(texto, historial)

    await guardar_mensaje(clave, "user", texto)
    await guardar_mensaje(clave, "assistant", respuesta)

    # Telegram tiene límite de 4096 caracteres por mensaje
    if len(respuesta) <= 4096:
        await update.message.reply_text(respuesta)
    else:
        for i in range(0, len(respuesta), 4096):
            await update.message.reply_text(respuesta[i:i+4096])


async def post_init(application: Application):
    await inicializar_db()
    logger.info("Base de datos inicializada")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")

    app = Application.builder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("clientes", cmd_clientes))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(CommandHandler("limpiar", cmd_limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot de Telegram iniciado. Esperando mensajes...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
