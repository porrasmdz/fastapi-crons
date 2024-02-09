from datetime import datetime
import os
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes,CallbackContext
import requests

TOKEN: Final = os.environ['TOKEN']
BOT_USERNAME: Final = os.environ['BOT_USERNAME']
API_URL = os.environ['API_URL']
API_ENDPOINT='/trips'

chat_ids = []


async def get_api_response():
    try:
        response = requests.get(API_URL+API_ENDPOINT)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()['total_registries']  # Convert response to JSON and return as dictionary
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)
        return {}
    
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"INFO | Se ejecutó el comando /start en el chat {update.message.chat.id} - {datetime.now()}")
    await update.message.reply_text("¡Saludos! Mi propósito es proveer información relevante sobre las carreras realizadas por agentes de nuestra empresa.")
    

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"INFO | Se ejecutó el comando /help en el chat {update.message.chat.id} - {datetime.now()}")
    await update.message.reply_text("Como solo soy una demostración no tengo comandos programados actualmente.")


async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"INFO | Se ejecutó el comando /setup en el chat {update.message.chat.id} - {datetime.now()}")
    await update.message.reply_text("A continuación, empezará a recibir actualizaciones de nuestra base de datos cada 15 minutos. Para dejar de recibirlas use el comando /stop")
    schedule_query(update, context)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"INFO | Se ejecutó el comando /test en el chat {update.message.chat.id} - {datetime.now()}")
    message = await query_db()
    await update.message.reply_text(message)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"INFO | Se ejecutó el comando /stop en el chat {update.message.chat.id} - {datetime.now()}")
    chat_id = update.message.chat.id

    if update.message.chat.id in chat_ids:
        chat_ids.remove(chat_id)
        await update.message.reply_text("Ha sido eliminado de la suscripcion satisfactoriamente.")
        return 
    
    await update.message.reply_text("Lo siento, usted no se encuentra suscrito actualmente")

async def query_db():
    response = await get_api_response()
    return f"Saludos! Nuestro total de carreras realizadas hasta ahora es de: {response}"

async def query_and_reply(context:CallbackContext):
    message = await query_db()
    for chat_id in chat_ids:
        print(f"SUSCRIPTION_QUEUE | Enviando mensaje recurrente a {chat_id} - {datetime.now()}")
        await context.bot.send_message(chat_id=chat_id, text=message)

def schedule_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(chat_ids) == 0:
        job_queue = context.job_queue
        job_queue.run_repeating(
            callback=query_and_reply, interval= 60*15,
        )
    chat_id = update.message.chat.id

    if(chat_id not in chat_ids):
        print(f"INFO | Se agendó queries recurrentes en el chat {chat_id} - {datetime.now()}")
        chat_ids.append(chat_id)
    else:
        print(f"ERROR | Se intentó agendar una tarea en el chat {chat_id}...¡Pero ya está agendada!- {datetime.now()}")
        
    

#Responses
def handle_responses(text:str)-> str:
    processed: str = text.lower()
    if 'hola' in processed:
        return 'Hola'
    
    if 'buenos dias' in processed:
        return 'Buenos días'
    
    if 'buenas tardes' in processed:
        return 'Buenas tardes'
    
    if 'buenas noches' in processed:
        return 'Buenas noches'
    
    return 'Lo siento, no tengo una respuesta para eso, solo soy una demostración.'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type :str = update.message.chat.type
    text : str = update.message.text
    print(f"User({update.message.chat.id}) in {message_type}: {text}")
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text :str = text.replace(BOT_USERNAME, '')
            response :str = handle_responses(new_text)
        else: 
            return
    else: 
        response: str = handle_responses(text)
    print("Bot:", response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update.message} causó el sgt. error {context.error}")

if __name__ == '__main__':
    print("Starting Bot...")
    app = Application.builder().token(TOKEN).build()

    #CMDS
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('setup', setup_command))
    app.add_handler(CommandHandler('stop', stop_command))
    app.add_handler(CommandHandler('test', test_command))
    

    #Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #Errors
    app.add_error_handler(error)

    

    print("Polling...")
    app.run_polling(poll_interval=3)