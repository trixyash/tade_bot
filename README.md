# 🤖 Binance Futures Testnet Trading Bot

A clean, well-structured Python CLI trading bot for placing **Market** and **Limit** orders on [Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M).

Built for the **Primetrade.ai Python Developer Intern Assessment**.

---

## ✨ Features

- ✅ Place **MARKET** and **LIMIT** orders (BUY & SELL)
- ✅ Two CLI modes: **direct flags** (`place`) and **guided prompts** (`interactive`)
- ✅ Beautiful output with Rich — colored tables, spinners, and panels
- ✅ Full input validation with clear error messages
- ✅ Structured logging to timestamped log files
- ✅ Clean architecture: API layer, business logic, validators, and CLI are all separate

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Binance REST API wrapper (auth + HTTP)
│   ├── orders.py            # Order placement logic
│   ├── validators.py        # Input validation
│   └── logging_config.py   # Structured file logging setup
├── logs/                    # Auto-created; holds timestamped log files
├── cli.py                   # CLI entry point (Typer + Rich)
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone / extract the project

```bash
cd trading_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

> **Getting Testnet credentials:**
> 1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
> 2. Log in with your GitHub account
> 3. Click **API Key** → **Create**
> 4. Copy the key and secret into your `.env`

---

## 🚀 Usage

### Mode 1 — Direct (`place` command)

Supply all parameters as flags in one command.

```bash
# Market BUY
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Limit SELL
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 90000

# Market SELL on ETH
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1

# Limit BUY — skip confirmation prompt
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 50000 --yes
```

### Mode 2 — Interactive (guided prompts)

Step-by-step prompts with live validation. No flags needed.

```bash
python cli.py interactive
```

### Help

```bash
python cli.py --help
python cli.py place --help
python cli.py interactive --help
```

---

## 📋 CLI Options (`place` command)

| Option | Short | Required | Description |
|---|---|---|---|
| `--symbol` | `-s` | ✅ | Trading pair e.g. `BTCUSDT` |
| `--side` | | ✅ | `BUY` or `SELL` |
| `--type` | `-t` | ✅ | `MARKET` or `LIMIT` |
| `--quantity` | `-q` | ✅ | Amount to trade e.g. `0.01` |
| `--price` | `-p` | ✅ (LIMIT) | Limit price e.g. `65000` |
| `--yes` | `-y` | ❌ | Skip confirmation prompt |

---

## 📝 Logging

Every session writes a log file to `logs/trading_bot_YYYYMMDD_HHMMSS.log`.

Each log entry includes:
- Timestamp
- Log level
- Module name
- Request parameters (signature excluded)
- Full API responses
- Validation events
- Errors with context

**Sample log output:**

```
2025-01-15 14:23:01 | INFO     | bot.client            | → Request  | POST /fapi/v1/order | Params: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': 0.01, 'timestamp': 1736951381000}
2025-01-15 14:23:01 | INFO     | bot.client            | ← Response | {'orderId': 3914928, 'symbol': 'BTCUSDT', 'status': 'FILLED', ...}
```

---

## 🧪 Assumptions

1. All orders are placed on **Binance Futures Testnet** (USDT-M perpetual). No real funds are used.
2. LIMIT orders use **GTC** (Good Till Cancelled) as `timeInForce`.
3. API credentials are loaded from a `.env` file using `python-dotenv`.
4. The minimum quantity is `0.001` — Binance may enforce higher minimums depending on symbol.
5. Python 3.8+ is required.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP calls to Binance REST API |
| `rich` | Beautiful terminal output (tables, spinners, panels) |
| `typer` | CLI framework with argument parsing |
| `python-dotenv` | Load `.env` credentials |

---

## 🏗️ Architecture

```
cli.py (typer + rich)
  │
  ├── validators.py     — Validates all inputs before touching the API
  │
  └── orders.py         — Business logic (MARKET / LIMIT dispatch)
        │
        └── client.py   — Signs requests, calls REST API, handles errors
```

Each layer has a single responsibility. The CLI knows nothing about signing. The client knows nothing about order types.

---

*Built by [Your Name] · Primetrade.ai Python Developer Assessment*
