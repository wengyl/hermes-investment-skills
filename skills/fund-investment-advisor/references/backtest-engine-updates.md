## Stop-Loss Strategy Comparison

See **references/stop-loss-backtest.md** for detailed results comparing fixed vs dynamic stop-loss thresholds across 10 funds over 1 year.

**TL;DR**: Fixed stop-loss (-8% to -15%) underperforms pure holding by ~7%. Dynamic stop-loss (base -12%, widens in bearish sentiment) is optimal — nearly matches pure holding while catching genuinely broken funds.

## Adding New Funds

See **references/adding-new-fund.md** for the complete 6-file checklist when adding a fund to the system.

## Per-Fund Stop-Loss Override

See **references/stop-loss-backtest.md** section "Per-Fund Stop-Loss Override" for the YAML + code pattern to set individual stop-loss levels per fund.
