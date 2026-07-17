# Financial Market Research Reference

Multi-source financial market analysis: gather real-time data, institutional research, and news, then synthesize structured multi-factor analysis.

## Data Sources

### Real-Time Prices (API)
- **gold-api.com**: `curl -s "https://api.gold-api.com/price/XAU"` — returns JSON with `price` (USD/oz), `updatedAt`. Free, no auth needed.
- Other symbols available: XAG (silver), etc.

### Institutional Research
- **World Gold Council (gold.org/goldhub)**: Gold ETF flows, central bank buying, market commentary, demand trends. Updated weekly.
  - Research library: `gold.org/goldhub/research/library`
  - Price data: `gold.org/goldhub/data/gold-prices` (CNY/oz display)
  - Key reports: Gold Market Commentary, Gold ETF Flows, Gold Demand Trends, Central Bank Statistics

### Chinese Financial News
- **Eastmoney (eastmoney.com)**: `/a/cywjh.html` — latest macro/finance news headlines with summaries. Good for event-driven analysis.
- **Sina Finance**: `/money/forex/` — forex and rate news (may block scraping)

### Central Bank / Macro Data
- Fed rate decisions: check CME FedWatch or news aggregators
- Non-farm payroll: reported monthly, moves rate expectations significantly

## Analysis Framework

When asked to analyze an asset or market, cover these dimensions:

1. **Price & Technicals**: Current price, recent trend, key levels
2. **Rate/Policy Environment**: Central bank stance, rate expectations, inflation
3. **Fund Flows**: ETF flows, institutional positioning
4. **Central Bank Activity**: Official sector buying/selling
5. **Geopolitical Factors**: Conflicts, trade tensions, sanctions
6. **Supply/Demand Fundamentals**: Physical market, production, consumption
7. **Scenario Analysis**: Present 2-3 scenarios with probabilities and price targets
8. **Actionable Summary**: Short/medium/long-term view with clear recommendations

## Output Format Preferences

User prefers structured analysis with:
- Tables for data comparison
- Emoji section headers for visual scanning
- Clear probability-weighted scenario breakdown
- Explicit risk disclaimers
- Chinese language output (user communicates in Chinese)

## Pitfalls

- **Gold price unit**: gold-api.com returns USD/oz. WGC displays CNY/oz. Always specify currency.
- **WGC article URLs**: Don't guess URL slugs from titles — navigate via the research library and click through. URL patterns are inconsistent.
- **Google/Bing scraping**: Blocked by bot detection. Use eastmoney.com or direct API calls instead.
- **Reuters**: Uses DataDome device check, blocks automated access. Avoid for scraping.
- **Rate impact on gold**: Conventional wisdom says rate hikes are bearish for gold, but WGC research argues hikes can actually be bullish (inflation confirmation, real rates still negative). Present both perspectives.
