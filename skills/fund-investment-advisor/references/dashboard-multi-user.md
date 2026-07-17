# Dashboard v3: Multi-User + Manual Import

## Overview

v3 adds **multi-user support** (login/register/session auth) and **manual import** (single fund lookup + batch paste) to the Flask dashboard.

## Architecture changes from v2

### users table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### holdings / transactions / dca_plans — added `user_id` column

Each user sees only their own data. Originally admins see all holdings.

```sql
ALTER TABLE holdings ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE transactions ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE dca_plans ADD COLUMN user_id INTEGER REFERENCES users(id);
```

All queries filtered by `WHERE user_id = ?` using the session's user.

## Flask auth pattern

```python
from flask import session

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-here')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_get_user(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect('/')
    return render_template_string(LOGIN_HTML)
```

Decorator pattern for auth-protected routes:

```python
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated
```

## Custom password hashing (Python 3.9 compatibility)

**Critical**: Python 3.9's `hashlib` lacks `scrypt()` in some builds (e.g., Apple's system Python 3.9). Do NOT use `werkzeug.security.generate_password_hash` — it calls `hashlib.scrypt` internally and crashes with `AttributeError: module 'hashlib' has no attribute 'scrypt'`.

Use custom pbkdf2-hmac-sha256 instead:

```python
import hashlib, hmac, secrets

def generate_password_hash(password, iterations=100000):
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    return f"pbkdf2:sha256:{iterations}:{salt}:{dk.hex()}"

def check_password_hash(pwhash, password):
    try:
        parts = pwhash.split(':')
        if len(parts) != 5: return False
        _, algo, iterations, salt, stored_hash = parts
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(dk.hex(), stored_hash)
    except Exception:
        return False
```

## Manual import API

### Single fund import

```
POST /api/import_fund
Content-Type: application/json

{"fund_code":"002112","fund_name":"德邦鑫星","share_count":931.09,
 "avg_cost":3.5264,"total_invested":1509.68,"total_withdrawn":0}
```

- `fund_code` is required; other fields optional (default to 0)
- Checks `fund_categories` for stop-loss/take-profit — inserts default (-10%/20%) if not found

### Fund name auto-lookup

```
POST /api/fund_lookup
Content-Type: application/json

{"fund_code":"002112"}
```

Returns:

```json
{
  "fund_name": "德邦鑫星价值灵活配置混合C",
  "category": {"category": "其他", "stop_loss": -10, "take_profit": 20, "theme": "其他"}
}
```

Backend: calls `curl -s "http://fundgz.1234567.com.cn/js/{code}.js"` and parses the JSONP callback for `name` field. If the JSONP call fails, falls back to akshare `fund_open_fund_info_em(code)` from subprocess.

### Batch import

```
POST /api/import_batch
Content-Type: application/json

{"text":"014414,4300.83,0.862,3707.49,0\n017731,325.59,4.5262,1500,0"}
```

Format per line: `code, share_count, avg_cost, total_invested, total_withdrawn`
Returns: `{"results": [{"line": 1, "ok": true}, ...]}`

### Transaction recording

```
POST /api/add_transaction
Content-Type: application/json

{"fund_code":"017731","trans_type":"buy","trans_date":"2026-07-13",
 "amount":100,"price":4.5262,"remark":"DCA定投"}
```

Updates `holdings.share_count` accordingly (adds on buy, subtracts on sell).

### Delete holding

```
POST /api/delete_holding
Content-Type: application/json

{"fund_code":"002112"}
```

Deletes the holding row for the current user.

### Refresh NAV

```
POST /api/refresh_nav
Content-Type: application/json
```

Fetches real-time estimates for ALL user's funds from `fundgz.1234567.com.cn`.

### Admin user management

```
GET /api/users  (admin only)
POST /api/delete_user  (admin only) {"user_id": 2}
```

## Frontend UI

Login page: simple form at `/login`, redirects to `/` on success.
Register page: `/register` (username + display_name + password).

Top-right user menu after login:
- "用户管理" (admin only — shows user table with delete/reset-password)
- "修改密码"
- "退出登录"

New user registrations are non-admin by default. Only existing admins can promote users.

## Deployment

No dependency changes from v2 (flask, plotly). Just restart:
```bash
kill $(lsof -ti :8787) && cd ~/.hermes/fund-advisor/dashboard && python3 app.py
```

First run auto-creates `admin` user with password `<change-me>`. Always change password after first login.
