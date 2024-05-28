from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO
import asyncio, ssl, certifi, json
import aiomqtt

token=os.environ["TB_TOKEN"]
device_id=os.environ["DEVICE_ID"]

tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
tls_context.verify_mode = ssl.CERT_REQUIRED
tls_context.check_hostname = True
tls_context.load_default_certs()

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["temperatura", "gráfico temperatura"],
        ["humedad", "gráfico humedad"],["destello"], 
        ["modo auto", "modo manual"],
        ["rele ON", "rele OFF"]]
    await context.bot.send_message(update.message.chat.id, 
        text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, 
        text="Este bot fue creado por: \nFernando \nKleinubing")

async def kill(update: Update, context):
    logging.info(context.args)
    if context.args and context.args[0] == '@e':
        await context.bot.send_animation(update.message.chat.id, "CgACAgEAAxkBAAOPZkuctzsWZVlDSNoP9PavSZmH5poAAmUCAALrx0lEVKaX7K-68Ns1BA")
        await asyncio.sleep(6)
        await context.bot.send_message(update.message.chat.id, text="¡¡¡Ahora estan todos muertos!!!")
    else:
        await context.bot.send_message(update.message.chat.id, text="☠️ ¡¡¡Esto es muy peligroso!!! ☠️")
        
async def medicion(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text} FROM mediciones ORDER BY timestamp DESC LIMIT 1"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        r = await cur.fetchone()
        if update.message.text == 'temperatura':
            unidad = 'ºC'
        else:
            unidad = '%'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()

async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text.split()[1]} FROM mediciones where id mod 2 = 0 AND timestamp >= '2024-04-23' - INTERVAL 1 DAY ORDER BY timestamp"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))
        fecha,var=zip(*filas)
        ax.plot(fecha,var)
        ax.grid(True, which='both')
        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('fecha')
        ax.set_ylabel('unidad')

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
    conn.close()

async def destello(update: Update, context):

    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        await client.publish(f"iot2024/{device_id}/destello", 1, qos=1)

    await context.bot.send_message(update.message.chat.id, 
        text="ESP32 Usa Destello!")

#######################################################

async def set_modo(update: Update, context):

    if "auto" in update.message.text.lower():
        modo = "auto"
    else:
        modo = "manual"

    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        await client.publish(f"iot2024/{device_id}/modo", modo, qos=1)

    logging.info(f"Modo: {modo}")
    await context.bot.send_message(update.message.chat.id, 
        text=f"ESP32 ahora esta en modo {modo}!")

#######################################################

async def set_setpoint(update: Update, context):
    if context.args and context.args[0].isnumeric():
        val = int(context.args[0])
        
        async with aiomqtt.Client(
            os.environ["SERVIDOR"],
            username=os.environ["MQTT_USR"],
            password=os.environ["MQTT_PASS"],
            port=int(os.environ["PUERTO_MQTTS"]),
            tls_context=tls_context,
        ) as client:
            await client.publish(f"iot2024/{device_id}/setpoint", val, qos=1)
        
        await context.bot.send_message(update.message.chat.id, 
            text=f"Nuevo setpoint: {val} grados celcius")
    else:
        await context.bot.send_message(update.message.chat.id, 
            text="⚠️ Esperaba un NUMERO ⚠️")

async def set_periodo(update: Update, context):
    if context.args and context.args[0].isnumeric():
        val = int(context.args[0])
        
        async with aiomqtt.Client(
            os.environ["SERVIDOR"],
            username=os.environ["MQTT_USR"],
            password=os.environ["MQTT_PASS"],
            port=int(os.environ["PUERTO_MQTTS"]),
            tls_context=tls_context,
        ) as client:
            await client.publish(f"iot2024/{device_id}/periodo", val, qos=1)
        
        await context.bot.send_message(update.message.chat.id, 
            text=f"Nuevo periodo: {val} segundos")
    else:
        await context.bot.send_message(update.message.chat.id, 
            text="⚠️ Esperaba un NUMERO ⚠️")


async def set_rele(update: Update, context):
    if context.args and context.args[0].isnumeric():
        val = int(context.args[0])
        
        async with aiomqtt.Client(
            os.environ["SERVIDOR"],
            username=os.environ["MQTT_USR"],
            password=os.environ["MQTT_PASS"],
            port=int(os.environ["PUERTO_MQTTS"]),
            tls_context=tls_context,
        ) as client:
            await client.publish(f"iot2024/{device_id}/rele", val, qos=1)
        
        if val >= 0:
            modo = "ON"
        else:
            modo = "OFF"
            
        await context.bot.send_message(update.message.chat.id, 
            text=f"Nuevo estado del rele: {modo}")
    else:
        await context.bot.send_message(update.message.chat.id, 
            text="⚠️ Esperaba un NUMERO ⚠️")

       
async def set_rele_msg(update: Update, context):

    if "on" in update.message.text.lower() or "encendido" in update.message.text.lower():
        modo = "ON"
        val = 1
    elif "off" in update.message.text.lower() or "apagado" in update.message.text.lower():
        modo = "OFF"
        val = 0
    else:
        modo = "OFF"
        val = 0 #int(update.message.text.slit()[-1])

    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:
        await client.publish(f"iot2024/{device_id}/rele", val, qos=1)

    await context.bot.send_message(update.message.chat.id, 
        text=f"Nuevo estado del rele: {modo}")


################################## MAIN #######################################
def main():
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('about', acercade))
    application.add_handler(CommandHandler('kill', kill))
    application.add_handler(MessageHandler(filters.Regex("^(temperatura|humedad)$"), medicion))
    application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico humedad)$"), graficos))

    application.add_handler(MessageHandler(filters.Regex("^destello$"), destello))
    application.add_handler(MessageHandler(filters.Regex("^modo"), set_modo))
    application.add_handler(CommandHandler('setpoint', set_setpoint))
    application.add_handler(CommandHandler('periodo', set_periodo))
    application.add_handler(CommandHandler('rele', set_rele))
    application.add_handler(MessageHandler(filters.Regex("^rele"), set_rele_msg))
    application.run_polling()

if __name__ == '__main__':
    main()
