# MuskEmpireBot
🖱️ clicker for [https://t.me/muskempire_bot](https://t.me/muskempire_bot/game?startapp=hero558455838)


# 🔥🔥 Use : PYTHON 3.10 🔥🔥

## Functionality
| Feature                               | Supported  |
|---------------------------------------|:----------:|
| Multithreading                        |     ✅     |
| Binding a proxy to a session          |     ✅     |
| Sleep before run each session         |     ✅     |
| Claim daily grant                     |     ✅     |
| Claim reward for friends              |     ✅     |
| Claim reward for completed quests     |     ✅     |
| Claim offline bonus                   |     ✅     |
| Automatic taps                        |     ✅     |
| PvP negotiations                      |     ✅     |
| Daily quiz and rebus solution         |     ✅     |
| Investing in funds (combo for profit) |     ✅     |
| Docker                                |     ✅     |


## [Options](https://github.com/sizifart/MuskEmpireBot/main/.env-example)

| Option                  | Description                                                       |
|-------------------------|-------------------------------------------------------------------|
| **API_ID / API_HASH**   | Platform data for launching a Telegram session                    |
| **TAPS_ENABLED**        | Taps enabled (True / False)                                       |
| **TAPS_PER_SECOND**     | Random number of taps per second (e.g. [20,30], max. 30)          |
| **PVP_ENABLED**         | PvP negotiations enabled (True / False)                           |
| **PVP_LEAGUE**          | League in negotiations (e.g. bronze)                              |
| **PVP_STRATEGY**        | Strategy in negotiations (e.g. random)                            |
| **PVP_COUNT**           | Number of negotiations per cycle (e.g. 10)                        |
| **INVEST_AMOUNT**       | Amount to invest in funds (e.g. 1400000)                          |
| **SLEEP_BETWEEN_START** | Sleep before start each session (e.g. [20, 360])                  |
| **ERRORS_BEFORE_STOP**  | The number of failed requests after which the bot will stop       |
| **USE_PROXY_FROM_FILE** | Whether to use proxy from the `proxies.txt` file (True / False)   |

## Prerequisites
You can obtain the **API_ID** and **API_HASH** after creating an application at [my.telegram.org/apps](https://my.telegram.org/apps)

**PvP negotiations** are disabled by default. Enable at your own risk. Upgrade your negotiation and ethics skills to win in case of a tie. The default strategy is randomly selected for each negotiation. If you wish, you can specify your own strategy, which will be used **in all** negotiations. League names for the **PVP_LEAGUE** parameter: `bronze`, `silver`, `gold`, `platina`, `diamond`. Strategy names for the **PVP_STRATEGY** parameter: `aggressive`, `flexible`, `protective`. The **PVP_COUNT** parameter determines the number of negotiations the bot will conduct in one cycle (the bot performs all actions, then sleeps for an hour, which is the recurring cycle).


## Prerequisites
Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/downloads/) 
- Telegram API_ID and API_HASH (you can get them [here](https://my.telegram.org/auth))

## Obtaining API Keys
1. Go to my.telegram.org and log in using your phone number.
2. Record the API_ID and API_HASH provided after registering your application in the .env file.

## Auto Install/Run
- Click on INSTALL.bat to automatically install the required dependencies 
- Then click on START.bat to run the project

## Menual Install/Run
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Please edit the name file .env-example to .env and add your API_ID and API_HASH:
   
## Usage
1. Run the bot:
   ```bash
   python main.py
   ```
 
# Telegram Channel

✅ Channel for information and training on Telegram airdrop bots 🔷 Follow us on Telegram : [SIZIFAIRDROP](https://t.me/sizifairdrop)

# Discussion

✅ If you have an question or something you can ask in here : [F.Davoodi](https://t.me/sizifart)
