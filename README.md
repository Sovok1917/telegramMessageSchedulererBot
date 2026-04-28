# Telegram Precision Scheduler

A Telegram userbot designed to schedule and send messages from a personal account with sub-millisecond precision. 

Standard scheduling tools and `asyncio.sleep()` functions often suffer from micro-delays or trigger early. This script utilizes a busy-wait loop for the final 100 milliseconds and synchronizes with Telegram's internal clock via standard NTP servers to guarantee messages are dispatched at the exact targeted boundary.

## Features
- **High Precision:** Uses a busy-wait loop to bypass Python's standard timer inaccuracies.
- **Remote Control:** Controlled entirely via a private, dedicated Telegram group.
- **Time Normalization:** Handles shorthand time inputs (e.g., `14:30` automatically resolves to `14:30:00.000`).
- **Clock Sync Verification:** Built-in tool to verify MTProto session time offset against Telegram servers.

## Prerequisites
- Python 3.8+
- A Telegram API ID and Hash (Get this from [my.telegram.org](https://my.telegram.org))
- `chrony` installed and running on the host system (required for accurate NTP sync)

### Setting up Host Time Sync (Linux)
To ensure the host machine's clock doesn't drift from Telegram's servers, use chrony instead of systemd-timesyncd:
```bash
sudo pacman -S chrony  # Use apt/dnf depending on the distro
sudo systemctl disable --now systemd-timesyncd
sudo systemctl enable --now chronyd
sudo chronyc makestep  # Force immediate sync
```

## Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/Sovok1917/telegramMessageSchedulererBot.git
cd telegramMessageSchedulererBot
```

2. **Set up the virtual environment**
```bash
python -m venv venv
source venv/bin/activate
pip install telethon python-dotenv
```

3. **Configure Credentials**
Create a `.env` file in the root directory. (Note: `.env` and `*.session` files should be ignored in git).
```env
API_ID=1234567
API_HASH=your_api_hash_here
SESSION_NAME=precisionSession
CONTROL_CHAT_ID=0
```
*Leave `CONTROL_CHAT_ID` as 0 for now. We will update this in the next step.*

4. **First Run & Authentication**
Start the bot to generate your session file.
```bash
python precisionBot.py
```
The terminal will prompt you for your phone number, the Telegram login code, and your 2FA password. Once authenticated, leave the script running.

5. **Set up the Control Chat**
- Open Telegram and create a new private group (e.g., "Scheduler Control").
- Send `/getChatId` in this new group. The bot will reply with a negative integer (e.g., `-100123456789`).
- Stop the bot (`Ctrl+C`), update the `CONTROL_CHAT_ID` in your `.env` file with this number, and restart the bot.

## Usage

All commands must be sent inside your configured Control Chat. The bot will ignore commands sent anywhere else.

### Commands

**1. Schedule a message**
```text
/send <target_chat> <time> <message>
```
*   `target_chat`: Can be a username (`@username`), phone number, or chat ID.
*   `time`: Accepts `HH:MM`, `HH:MM:SS`, or `HH:MM:SS.mmm`. Assumes the current day.
*   *Example:* `/send @testGroup 14:30:00.000 Hello everyone`

**2. Check Clock Synchronization**
```text
/sync
```
Returns the local clock offset from Telegram's servers. Ideally, this should read `0 seconds`.

**3. Get Chat ID**
```text
/getChatId
```
Returns the internal Telegram ID of the current chat
