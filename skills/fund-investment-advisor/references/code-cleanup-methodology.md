# Code Cleanup Methodology (2026-05-31)

## How to Identify Unused Scripts

### Step 1: Find Direct Imports
Check which modules the main scripts (advisor.py, morning_intraday.py, afternoon_intraday.py) actually import.

### Step 2: Trace Transitive Dependencies
For each module NOT directly imported, check if it's imported by an in-use module.

### Step 3: Classify Results
- **In-use**: Directly imported by main scripts
- **Indirectly used**: Imported by in-use modules (keep)
- **Dead code**: Not imported by anything in the active chain (archive)

## Cleanup Results

### Before: 44 Python files
### After: 19 core files

### Active Modules (19):
```
Main scripts (3):
  advisor.py              - Unified entry point
  morning_intraday.py     - Morning intraday report
  afternoon_intraday.py   - Afternoon intraday report

Strategy engines (3):
  adaptive_risk_v2.py     - Risk control engine
  oof_strategy_advisor.py - Strategy advisor
  oof_strategies.py       - Strategy implementations

Market analysis (3):
  market_mainline.py      - Market mainline tracking
  market_sentiment.py     - Market sentiment analysis
  history_comparison.py   - Historical returns comparison

Review modules (3):
  weekly_review.py        - Weekly review
  monthly_evaluation.py   - Monthly evaluation
  strategy_optimizer.py   - Strategy optimization

Data layer (3):
  data_fetcher.py         - Data fetching (Tencent API)
  multi_source_adapter.py - Multi-source adapter
  update_nav_curl.py      - NAV update via curl

Infrastructure (4):
  backtest_engine.py      - Backtest engine (includes OptimizedMAStrategy)
  db_init.py              - Database initialization
  user_config.py          - User configuration
  fund_categorizer.py     - Fund categorization

Data fetching (2, added 2026-05-31):
  fetch_history_nav.py    - Initial AKShare historical NAV fetch
  update_history_nav.py   - Incremental daily NAV update
```

### Archived (25 files → archive/):
- Test/debug scripts (6)
- Old strategy versions (8)
- Never-integrated modules (6)
- Utility scripts (5)

## Important: Database Path

The active database is `data/fund_system.db` (NOT `data/fund_advisor.db`).
`fund_advisor.db` is empty (0 bytes). Always use `fund_system.db` for backtesting.

## Pitfall: Checking Only Direct Imports

A module may be indirectly imported. Example:
- `backtest_engine.py` is NOT directly imported by advisor.py
- BUT it IS imported by `monthly_evaluation.py` and `weekly_review.py`
- Which ARE imported by advisor.py

Always trace the full import chain before archiving.
