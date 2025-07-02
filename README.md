# Python ETF Holdings Scraper

A lightweight Python script that uses reverse engineered APIs to fetch full ETF holdings data and live summary information from Schwab’s research portal.

---

## 🔍 Features

- Retrieves ETF summary:
  - Last price
  - Bid/ask
  - Volume
  - As-of date

- Retrieves full ETF holdings:
  - Symbol
  - Name
  - Weight (%)
  - Shares
  - Market value (USD)

---

## 📦 Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`

Install dependencies:

```bash
pip install -r requirements.txt
