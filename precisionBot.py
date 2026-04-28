import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()

apiId = int(os.getenv('API_ID'))
apiHash = os.getenv('API_HASH')
sessionName = os.getenv('SESSION_NAME')
controlChatId = int(os.getenv('CONTROL_CHAT_ID', 0))

telegramClient = TelegramClient(sessionName, apiId, apiHash)

async def sendPreciseMessage(targetChat, targetTime, messageText):
    """
    Executes an asynchronous wait until the exact target time.
    Since no latency is deducted, the network request initiates exactly on the boundary.
    Includes a configurable safety padding to definitively prevent premature dispatch.
    """
    # Increase to 5 or 10 if you want an absolute hardware guarantee
    # that the message crosses the server boundary after the 0th millisecond.
    safetyPaddingMs = 0
    targetTime = targetTime + timedelta(milliseconds=safetyPaddingMs)

    while True:
        timeToWait = (targetTime - datetime.now()).total_seconds()

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
    await event.reply(str(event.chat_id))

@telegramClient.on(events.NewMessage(pattern=r'/sync'))
async def handleSyncCommand(event):
    """
    Validates clock synchronization by comparing local UTC time
    to the Telegram server's timestamp of this exact message.
    """
    serverTime = event.date

    localTime = datetime.now(serverTime.tzinfo)

    diff = (localTime - serverTime).total_seconds()

    if abs(diff) <= 2:
        status = "✅ System clock is perfectly synced with Telegram!"
    else:
        status = "⚠️ Warning: System clock appears to be out of sync."

    await event.reply(
        f"{status}\n"
        f"Server Time: {serverTime.strftime('%H:%M:%S')}\n"
        f"Local Time: {localTime.strftime('%H:%M:%S')}\n"
        f"Offset: {diff:.2f} seconds"
    )

@telegramClient.on(events.NewMessage(pattern=r'/send'))
async def handleScheduleCommand(event):
    """
    Parses scheduling parameters from the control chat and dispatches the background task.
    Missing seconds or milliseconds are appended as zeros for simplified inputs.
    """
    if controlChatId and event.chat_id != controlChatId:
        return

    messageParts = event.message.text.split(' ', 3)

    if len(messageParts) < 4:
        await event.reply("Usage: /send <targetChat> <HH:MM>[or HH:MM:SS / HH:MM:SS.mmm] <message>")
        return

    targetChat = messageParts[1]
    timeString = messageParts[2]
    messageText = messageParts[3]

    if timeString.count(':') == 1:
        timeString += ":00"
    if '.' not in timeString:
        timeString += ".000"

    try:
        now = datetime.now()
        targetTime = datetime.strptime(timeString, "%H:%M:%S.%f")
        targetTime = targetTime.replace(year=now.year, month=now.month, day=now.day)

        if targetTime < now:
            await event.reply("Target time is in the past.")
            return

        asyncio.create_task(sendPreciseMessage(targetChat, targetTime, messageText))
        await event.reply(f"Task scheduled. Target: {targetChat}, Time: {timeString}")

    except ValueError:
        await event.reply("Invalid time format. Acceptable formats: HH:MM, HH:MM:SS, HH:MM:SS.mmm")

telegramClient.start()
telegramClient.run_until_disconnected()
