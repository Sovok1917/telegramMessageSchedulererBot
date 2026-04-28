import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()

apiId = int(os.getenv('API_ID'))
apiHash = os.getenv('API_HASH')
sessionName = os.getenv('SESSION_NAME')
controlChatId = int(os.getenv('CONTROL_CHAT_ID', 0))

telegramClient = TelegramClient(sessionName, apiId, apiHash)

async def sendPreciseMessage(targetChat, targetTime, messageText, latencyOffset):
    """
    Calculates the remaining time until targetTime and executes an asynchronous wait.
    Utilizes a busy-wait loop for the final 100 milliseconds to guarantee sub-millisecond
    precision, overcoming the scheduling inaccuracies inherent to asyncio.sleep().
    """
    while True:
        currentTime = datetime.now()
        timeToWait = (targetTime - currentTime).total_seconds()

        timeToWait -= latencyOffset

        if timeToWait > 0.1:
            await asyncio.sleep(timeToWait - 0.1)
        elif timeToWait > 0:
            pass
        else:
            break

    await telegramClient.send_message(targetChat, messageText)

    if controlChatId:
        await telegramClient.send_message(controlChatId, f"Message successfully dispatched to {targetChat}")

@telegramClient.on(events.NewMessage(pattern=r'/getChatId'))
async def handleGetChatId(event):
    """
    Resolves and returns the integer ID of the chat where the command was issued.
    """
    currentChatId = event.chat_id
    await event.reply(str(currentChatId))

@telegramClient.on(events.NewMessage(pattern=r'/send'))
async def handleScheduleCommand(event):
    """
    Parses scheduling parameters from the control chat and dispatches the background task.
    Validates the origin chat to ensure commands are only processed from the authorized control chat.
    """
    if controlChatId and event.chat_id != controlChatId:
        return

    messageParts = event.message.text.split(' ', 3)

    if len(messageParts) < 4:
        await event.reply("Usage: /send <targetChat> <HH:MM:SS.mmm> <message>")
        return

    targetChat = messageParts[1]
    timeString = messageParts[2]
    messageText = messageParts[3]

    try:
        now = datetime.now()
        targetTime = datetime.strptime(timeString, "%H:%M:%S.%f")
        targetTime = targetTime.replace(year=now.year, month=now.month, day=now.day)

        if targetTime < now:
            await event.reply("Target time is in the past.")
            return

        networkLatency = 0.045

        asyncio.create_task(sendPreciseMessage(targetChat, targetTime, messageText, networkLatency))
        await event.reply(f"Task scheduled. Target: {targetChat}, Time: {timeString}")

    except ValueError:
        await event.reply("Invalid time format. Required: HH:MM:SS.mmm")

telegramClient.start()
telegramClient.run_until_disconnected()
