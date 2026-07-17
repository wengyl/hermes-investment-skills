# Macro Signal Dashboard

## Overview

Script: `scripts/macro_dashboard.py`

Fetches 6 macroeconomic indicators from AKShare, scores each on a -2 to +2 scale, and produces a composite signal with position sizing advice.

## Data Sources

| Indicator | AKShare Function | Signal Logic |
|-----------|-----------------|--------------|
| PMI | `ak.macro_china_pmi()` | ≥51 bullish, 50 neutral, <50 bearish |
| CPI | `ak.macro_china_cpi_yearly()` | 1.5-3% bullish, 0.5-1.5% neutral, <0.5% bearish |
| M2/M1 | `ak.macro_china_money_supply()` | M1-M2 scissors >0 bullish (money flowing into economy) |
| LPR | `ak.macro_china_lpr()` | Rate cut = bullish, hike = bearish |
| GDP | `ak.macro_china_gdp_yearly()` | ≥5.5% strong, ≥5% ok, <4% weak |
| FX Reserves | `ak.macro_china_fx_reserves_yearly()` | Rising = bullish, falling = bearish |

## Scoring

- Each indicator: -2 to +2
- Max possible: +12 (6 indicators × 2)
- Min possible: -12

## Position Sizing

| Score % | Signal | Position Range |
|---------|--------|---------------|
| ≥50% | 🟢 Aggressive | 80%-100% |
| ≥20% | 🟢 Bullish | 60%-80% |
| ≥-20% | 🟡 Neutral | 50%-60% |
| ≥-50% | 🔴 Bearish | 40%-50% |
| <-50% | 🔴 Defensive | 30%-40% |

## Pitfalls

1. **AKShare `macro_china_shrzgm()` is broken** — returns `('No cipher can be selected.',)`. Use `macro_china_money_supply()` for M2/M1 data instead. Social financing (社融) data is not currently available via AKShare.

2. **PMI data is reverse-ordered** — `df.iloc[0]` is the LATEST month, not the oldest.

3. **Some indicators have stale data** — CPI/GDP/FX reserves may lag by months. Always check the `period` field and note staleness in the report.

4. **PMI boundary at exactly 50.0** — Should be treated as neutral (荣枯线), not bullish or bearish. The score gives +1 for ≥50 (still expansion territory) but signal is neutral.

## Usage

```bash
# Standalone
python3 scripts/macro_dashboard.py

# From advisor (future integration point)
# Call generate_dashboard() from morning/weekly reports
```

Output saved to: `data/macro_dashboard.json`
