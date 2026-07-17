# Data Cache Layer - Implementation Reference

## Architecture

```
data_cache.py
├── DataCache
│   ├── TTL settings per data type
│   ├── Memory cache (dict)
│   ├── File cache (JSON in data/cache/)
│   ├── get() / set() / clear_expired()
│   └── _cache_key() / _cache_path()
└── MultiSourceFetcher
    ├── fetch_with_retry() - curl with exponential backoff
    ├── get_a_share_index() - Tencent → Sina fallback
    ├── get_industry_data() - Sina industry data
    └── get_market_env() - bull/bear/shock from index
```

## Cache TTL

```python
TTL = {
    'index': 120,        # 2 minutes
    'industry': 600,     # 10 minutes
    'fund_nav': 7200,    # 2 hours
    'fund_info': 86400,  # 24 hours
    'market': 300,       # 5 minutes
}
```

## Data Sources

### A-Share Index
- Primary: Tencent (`qt.gtimg.cn`) - GBK encoding, ~35 fields per index
- Fallback: Sina (`hq.sinajs.cn`) - GBK encoding, different field layout

### Industry Data
- Primary: EastMoney push2 (`push2.eastmoney.com`) - may be blocked (HTTP 000)
- Fallback: Sina (`vip.stock.finance.sina.com.cn/q/view/newSinaHy.php`) - GBK, JavaScript variable format

## Sina Industry Data Format

```
var S_Finance_bankuai_sinaindustry = {
  "new_blhy": "new_blhy,玻璃行业,19,22.19,0.75,3.49,1101440952,25548830572,sh603601,10.005,23.530,2.140,再升科技",
  ...
}
```

Fields: code, name, stock_count, avg_price, price_change, change_pct, volume, amount, leader_code, leader_price, leader_change, leader_pct, leader_name

## Cache Directory

`~/.hermes/fund-advisor/data/cache/` - auto-created, contains JSON files keyed by MD5 hash.

## Retry Logic

```python
for attempt in range(max_retries + 1):
    try:
        result = subprocess.run(['curl', ...], timeout=timeout)
        if result.returncode == 0:
            return result.stdout.decode(encoding)
    except:
        if attempt < max_retries:
            time.sleep(1 * (attempt + 1))  # Exponential backoff
```

## Testing

```bash
cd ~/.hermes/fund-advisor/scripts && python3 data_cache.py
```
