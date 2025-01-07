# [![Static Badge](https://img.shields.io/badge/Telegram-Bot%20Link-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/Vanilla_Finance_Bot/Vanillafinance?startapp=inviteId10512928)

## Zoo Story BOT

> **Recommendation**: Use **Python 3.10**

---

# Features
| Feature                           | Supported |
|-----------------------------------|:---------:|
| Multithreading                    |     ✅     |
| Proxy binding to session (adv)    |     ✅     |
| User-Agent binding to session     |     ✅     |
| Support for `.session` files      |     ✅     |
| Auto registration in bot          |     ✅     |
| Auto-tasks                        |     ✅     |
| Daily rewards                     |     ✅     |
| Auto quizzes                      |     ✅     |
| Auto buy animals                  |     ✅     |
| Auto upgrade animals              |     ✅     |
| Advanced anti-detection           |     ✅     |

---

## [Settings](https://github.com/khondokerXhasan/Zoo-BOT/blob/master/.env-example/)

| Setting                     | Description                                                                                   | Default Value           |
|-----------------------------|-----------------------------------------------------------------------------------------------|-------------------------|
| **API_ID / API_HASH**       | Platform data required to run the Telegram session.                                           | Required for operation  |
| **USE_RANDOM_DELAY_IN_RUN** | Enables random delays during task execution to avoid detection.                               | `True`                  |
| **START_DELAY**             | Delay (in seconds) between session starts.                                                   | `[30, 60]`              |
| **AUTO_DO_TASKS**           | Enable or disable automatic task execution.                                                  | `True`                  |
| **AUTO_DO_QUIZZES**         | Enable or disable automatic quiz solving.                                                    | `True`                  |
| **AUTO_JOIN_CHANNELS**      | Automatically join Telegram channels.                                                        | `True`                  |
| **ARCHIVE_CHANNELS**        | Automatically archive joined channels.                                                       | `False`                 |
| **AUTO_BUY_ANIMALS**        | Automatically purchase animals in the game.                                                  | `True`                  |
| **MAX_ANIMALS**             | Maximum number of animals to buy.                                                           | `10`                    |
| **AUTO_UPGRADE_ANIMALS**    | Automatically upgrade animals.                                                               | `True`                  |
| **AUTO_FEED_ANIMALS**       | Automatically feed animals.                                                                  | `True`                  |
| **COIN_TO_SAVE**            | Amount of coins to save before spending.                                                     | `5000`                  |
| **REF_LINK**                | Referral link for the game.                                                                  | `'http://t.me/zoo_story_bot/game?startapp=ref1827015632'` |
| **SAVE_JS_FILES**           | Save JavaScript files (experimental).                                                        | `False`                 |
| **ADVANCED_ANTI_DETECTION** | Enable advanced anti-detection measures.                                                     | `True`                  |
| **ENABLE_SSL**              | Enable or disable SSL.                                                                       | `True`                  |
| **USE_PROXY_FROM_FILE**     | Use proxy settings from a file.                                                              | `False`                 |
| **GIT_UPDATE_CHECKER**      | Enable Git update checker for updates.                                                       | `True`                  |

---

## Quick Start 📚

To install dependencies and run the bot quickly, use the provided batch file (`run.bat`) for Windows or the shell script (`run.sh`) for Linux.

### Prerequisites
Ensure you have **Python 3.10 or Greater** installed.

### Obtaining API Keys
1. Go to [my.telegram.org](https://my.telegram.org) and log in.
2. Under **API development tools**, create a new application to get your `API_ID` and `API_HASH`, and add these to your `.env` file.

---

## Installation

### Clone the Repository
```shell
git clone https://github.com/khondokerXhasan/Zoo-BOT
cd Zoo-BOT
```

Then you can do automatic installation by typing:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

# Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
python3 main.py
```

You can also use arguments for quick start, for example:
```shell
~/Zoo-BOT >>> python3 main.py --action (1/2)
# Or
~/Zoo-BOT >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
python main.py
```

You can also use arguments for quick start, for example:
```shell
~/Zoo-BOT >>> python main.py --action (1/2)
# Or
~/Zoo-BOT >>> python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

## Usage
1. **First Launch**: Create a session with the `--action 2` option. This will create a `sessions` folder for storing all accounts and an `accounts.json` configuration file.
2. **Existing Sessions**: If you already have sessions, add them to the `sessions` folder and run the bot with the clicker mode.

### Example of `accounts.json`
```json
[
  {
    "session_name": "name_example",
    "user_agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
    "proxy": "type://user:pass:ip:port"  // "proxy": "" if no proxy
  }
]
```

### Contacts

[Join our Telegram Channel](https://t.me/scripts_hub)
