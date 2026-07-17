# Fund-Level Stop-Loss Override

## Feature (added 2026-06-04)

Fund categories have default stop_loss/take_profit, but individual funds can override.

### YAML Config: `configs/fund_categories.yaml`

```yaml
行业指数基金:
  stop_loss: -12      # category default
  take_profit: +15
  funds:
    - code: "014414"
      name: "招商中证畜牧养殖ETF联接A"
      stop_loss: -15   # fund-level override (takes priority)
```

### Code: `scripts/fund_categorizer.py`

```python
result = {
    'stop_loss': (fund_detail or {}).get('stop_loss', category_info.get('stop_loss', -15)),
    'take_profit': (fund_detail or {}).get('take_profit', category_info.get('take_profit', +20)),
}
```

### Verification

```bash
python3 -c "
from fund_categorizer import FundCategorizer
c = FundCategorizer()
info = c.get_fund_info('014414', '招商畜牧')
print(f'SL: {info[\"stop_loss\"]}%')  # -15 (fund-level)
info2 = c.get_fund_info('999999', '测试ETF联接C')
print(f'SL: {info2[\"stop_loss\"]}%')  # -12 (category-level)
"
```

## Pitfalls

1. Must add `stop_loss` key under the specific fund entry in YAML, not just at category level
2. Code must check `(fund_detail or {}).get('stop_loss', category_info.get(...))` — NOT `category_info.get(...)` alone
3. If fund_detail is None (fund not in YAML), falls back to category default correctly
