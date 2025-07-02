from etf_scraper import scrape_etf

summary, holdings = scrape_etf("VTI", 100)

print("ETF Summary:")
print(summary)
print(holdings)
