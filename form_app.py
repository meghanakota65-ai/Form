# """
# form_app.py
# ===========
# LocalAI TV — Web Form for Manual Price Entry

# Run:
#     pip install flask
#     python form_app.py

# Then open: http://localhost:5001
# Share on your network: http://<your-ip>:5001
# """

# import sqlite3
# import json
# import re
# from datetime import date, datetime
# from pathlib import Path
# from flask import Flask, render_template_string, request, redirect, url_for, jsonify

# # ── Path config — adjust if running from a different folder ──────────────────
# BASE_DIR        = Path(__file__).parent
# DB_PATH         = BASE_DIR / "db" / "prices.db"
# MASTER_VEG_FILE = BASE_DIR / "db" / "master_vegetables.json"

# app = Flask(__name__)

# # ─────────────────────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────────────────────

# def load_master_vegetables() -> list:
#     if not MASTER_VEG_FILE.exists():
#         return []
#     with open(MASTER_VEG_FILE, encoding="utf-8") as f:
#         data = json.load(f)
#     return data.get("vegetables", [])


# def get_db():
#     DB_PATH.parent.mkdir(parents=True, exist_ok=True)
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     # Ensure table + columns exist
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS prices (
#             id            INTEGER PRIMARY KEY AUTOINCREMENT,
#             date          TEXT NOT NULL,
#             sno           INTEGER,
#             name_telugu   TEXT NOT NULL,
#             price         REAL,
#             price_display TEXT NOT NULL DEFAULT '',
#             grade         TEXT DEFAULT 'I',
#             price_type    TEXT DEFAULT 'per_kg',
#             price_raw     TEXT,
#             created_at    TEXT
#         )
#     """)
#     # Add missing columns to existing DB (safe to call each time)
#     existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(prices)").fetchall()]
#     for col, defn in [
#         ("price_type", "TEXT DEFAULT 'per_kg'"),
#         ("price_raw",  "TEXT"),
#         ("sno",        "INTEGER"),
#         ("price_display", "TEXT NOT NULL DEFAULT ''"),
#     ]:
#         if col not in existing_cols:
#             conn.execute(f"ALTER TABLE prices ADD COLUMN {col} {defn}")
#     conn.commit()
#     return conn


# def is_per_piece(raw) -> bool:
#     if raw is None:
#         return False
#     s = str(raw).strip()
#     parts = s.split("/")
#     if len(parts) == 2:
#         try:
#             float(parts[0].strip())
#             float(parts[1].strip())
#             return True
#         except ValueError:
#             pass
#     return False


# def parse_price(raw):
#     if raw is None or str(raw).strip() in ("", "null", "none"):
#         return None
#     s = str(raw).strip()
#     if "/" in s:
#         parts = s.split("/")
#         try:
#             return float(parts[1].strip())  # store the rate
#         except ValueError:
#             pass
#         s = parts[0].strip()
#     s = re.sub(r"[^\d.]", "", s)
#     try:
#         return float(s) if s else None
#     except ValueError:
#         return None


# def format_price_display(raw, price_type: str) -> str:
#     if not raw or str(raw).strip() in ("", "null"):
#         return "తెలియలేదు"
#     if price_type == "per_piece" and "/" in str(raw):
#         parts = str(raw).split("/")
#         try:
#             count = int(float(parts[0].strip()))
#             rate  = int(float(parts[1].strip()))
#             return f"Pcs {count}/{rate} Rs"
#         except (ValueError, IndexError):
#             pass
#     val = parse_price(raw)
#     return f"Rs.{int(val)}" if val is not None else "తెలియలేదు"


# def get_existing_prices(price_date: str) -> dict:
#     """Return {name_telugu: row} for a given date."""
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT name_telugu, price, price_type, price_raw, sno FROM prices WHERE date=? ORDER BY sno",
#         (price_date,)
#     ).fetchall()
#     conn.close()
#     return {r["name_telugu"]: dict(r) for r in rows}


# def save_prices(form_data: dict, price_date: str) -> int:
#     conn  = get_db()
#     saved = 0
#     conn.execute("DELETE FROM prices WHERE date=?", (price_date,))
#     for sno, name in enumerate(form_data["names"], 1):
#         raw_price  = form_data["prices"][sno - 1].strip()
#         price_type = form_data["price_types"][sno - 1]

#         if not raw_price:
#             raw_price_val = None
#             price_type    = "per_kg"
#         elif is_per_piece(raw_price):
#             price_type = "per_piece"
#             price_type_val = "per_piece"
#         else:
#             price_type_val = price_type

#         price_val     = parse_price(raw_price) if raw_price else None
#         price_display = format_price_display(raw_price or None, price_type_val if raw_price else "per_kg")
#         price_raw     = raw_price if raw_price else None

#         conn.execute(
#             """INSERT INTO prices
#                (date, sno, name_telugu, price, price_display, grade, price_type, price_raw, created_at)
#                VALUES (?, ?, ?, ?, ?, 'I', ?, ?, ?)""",
#             (
#                 price_date, sno, name.strip(),
#                 price_val, price_display,
#                 price_type_val if raw_price else "per_kg",
#                 price_raw,
#                 datetime.now().isoformat()
#             )
#         )
#         saved += 1
#     conn.commit()
#     conn.close()
#     return saved


# def get_all_dates():
#     if not DB_PATH.exists():
#         return []
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT date, COUNT(*) as cnt FROM prices GROUP BY date ORDER BY date DESC LIMIT 30"
#     ).fetchall()
#     conn.close()
#     return [dict(r) for r in rows]


# # ─────────────────────────────────────────────────────────────────────────────
# # HTML TEMPLATE
# # ─────────────────────────────────────────────────────────────────────────────

# HTML = """<!DOCTYPE html>
# <html lang="te">
# <head>
# <meta charset="UTF-8">
# <meta name="viewport" content="width=device-width, initial-scale=1.0">
# <title>LocalAI TV — ధర నమోదు</title>
# <link href="https://fonts.googleapis.com/css2?family=Tiro+Telugu&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
# <style>
#   :root {
#     --bg:       #0d1117;
#     --surface:  #161b22;
#     --border:   #30363d;
#     --gold:     #f5c518;
#     --gold-dim: #c49b12;
#     --green:    #3fb950;
#     --red:      #f85149;
#     --text:     #e6edf3;
#     --muted:    #8b949e;
#     --input-bg: #0d1117;
#   }

#   * { box-sizing: border-box; margin: 0; padding: 0; }

#   body {
#     background: var(--bg);
#     color: var(--text);
#     font-family: 'DM Sans', sans-serif;
#     min-height: 100vh;
#   }

#   /* ── Header ── */
#   header {
#     background: var(--surface);
#     border-bottom: 1px solid var(--border);
#     padding: 1rem 1.5rem;
#     display: flex;
#     align-items: center;
#     justify-content: space-between;
#     position: sticky;
#     top: 0;
#     z-index: 100;
#   }
#   .brand { display: flex; align-items: center; gap: 10px; }
#   .brand-dot {
#     width: 10px; height: 10px; border-radius: 50%;
#     background: var(--gold);
#     box-shadow: 0 0 8px var(--gold);
#     animation: pulse 2s ease-in-out infinite;
#   }
#   @keyframes pulse {
#     0%,100% { opacity: 1; } 50% { opacity: 0.4; }
#   }
#   .brand-name {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.85rem;
#     color: var(--gold);
#     letter-spacing: 0.08em;
#     font-weight: 500;
#   }
#   .header-date {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.75rem;
#     color: var(--muted);
#   }

#   /* ── Layout ── */
#   main {
#     max-width: 860px;
#     margin: 0 auto;
#     padding: 2rem 1rem 4rem;
#   }

#   /* ── Date picker bar ── */
#   .date-bar {
#     display: flex;
#     align-items: center;
#     gap: 12px;
#     margin-bottom: 1.5rem;
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 10px;
#     padding: 0.75rem 1rem;
#   }
#   .date-bar label {
#     font-size: 0.8rem;
#     color: var(--muted);
#     white-space: nowrap;
#   }
#   .date-bar input[type="date"] {
#     background: var(--input-bg);
#     border: 1px solid var(--border);
#     color: var(--text);
#     border-radius: 6px;
#     padding: 6px 10px;
#     font-family: 'DM Mono', monospace;
#     font-size: 0.85rem;
#     cursor: pointer;
#   }
#   .date-bar input[type="date"]:focus {
#     outline: none;
#     border-color: var(--gold);
#   }
#   .btn-load {
#     background: transparent;
#     border: 1px solid var(--gold);
#     color: var(--gold);
#     padding: 6px 14px;
#     border-radius: 6px;
#     font-size: 0.8rem;
#     cursor: pointer;
#     font-family: 'DM Mono', monospace;
#     transition: background 0.15s;
#   }
#   .btn-load:hover { background: rgba(245,197,24,0.1); }

#   /* ── Flash messages ── */
#   .flash {
#     padding: 0.75rem 1rem;
#     border-radius: 8px;
#     margin-bottom: 1rem;
#     font-size: 0.9rem;
#     display: flex;
#     align-items: center;
#     gap: 8px;
#   }
#   .flash.success { background: rgba(63,185,80,0.15); border: 1px solid rgba(63,185,80,0.4); color: var(--green); }
#   .flash.error   { background: rgba(248,81,73,0.15);  border: 1px solid rgba(248,81,73,0.4);  color: var(--red); }

#   /* ── Table ── */
#   .price-table-wrap {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 12px;
#     overflow: hidden;
#     margin-bottom: 1.5rem;
#   }
#   .table-header {
#     display: grid;
#     grid-template-columns: 48px 1fr 160px 120px;
#     gap: 0;
#     background: #1c2128;
#     border-bottom: 1px solid var(--border);
#     padding: 0.6rem 1rem;
#   }
#   .table-header span {
#     font-size: 0.7rem;
#     font-family: 'DM Mono', monospace;
#     color: var(--muted);
#     letter-spacing: 0.06em;
#     text-transform: uppercase;
#   }

#   .veg-row {
#     display: grid;
#     grid-template-columns: 48px 1fr 160px 120px;
#     gap: 0;
#     align-items: center;
#     border-bottom: 1px solid rgba(48,54,61,0.5);
#     padding: 0.4rem 1rem;
#     transition: background 0.1s;
#   }
#   .veg-row:last-child { border-bottom: none; }
#   .veg-row:hover { background: rgba(255,255,255,0.02); }

#   .sno {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.75rem;
#     color: var(--muted);
#   }

#   .veg-name {
#     font-family: 'Tiro Telugu', serif;
#     font-size: 1rem;
#     color: var(--text);
#     padding-right: 12px;
#   }

#   .price-input {
#     background: var(--input-bg);
#     border: 1px solid var(--border);
#     color: var(--text);
#     border-radius: 6px;
#     padding: 7px 10px;
#     font-family: 'DM Mono', monospace;
#     font-size: 0.88rem;
#     width: 100%;
#     transition: border-color 0.15s;
#   }
#   .price-input:focus {
#     outline: none;
#     border-color: var(--gold);
#     box-shadow: 0 0 0 3px rgba(245,197,24,0.1);
#   }
#   .price-input::placeholder { color: #444d56; }

#   .type-select {
#     background: var(--input-bg);
#     border: 1px solid var(--border);
#     color: var(--muted);
#     border-radius: 6px;
#     padding: 7px 8px;
#     font-size: 0.75rem;
#     font-family: 'DM Mono', monospace;
#     margin-left: 8px;
#     cursor: pointer;
#     transition: border-color 0.15s;
#   }
#   .type-select:focus { outline: none; border-color: var(--gold); }

#   /* ── Actions ── */
#   .actions {
#     display: flex;
#     gap: 12px;
#     align-items: center;
#   }

#   .btn-save {
#     background: var(--gold);
#     color: #000;
#     border: none;
#     padding: 10px 28px;
#     border-radius: 8px;
#     font-size: 0.9rem;
#     font-weight: 600;
#     cursor: pointer;
#     font-family: 'DM Sans', sans-serif;
#     transition: transform 0.1s, background 0.15s;
#   }
#   .btn-save:hover { background: var(--gold-dim); }
#   .btn-save:active { transform: scale(0.97); }

#   .btn-clear {
#     background: transparent;
#     border: 1px solid var(--border);
#     color: var(--muted);
#     padding: 10px 20px;
#     border-radius: 8px;
#     font-size: 0.85rem;
#     cursor: pointer;
#     font-family: 'DM Sans', sans-serif;
#     transition: border-color 0.15s, color 0.15s;
#   }
#   .btn-clear:hover { border-color: var(--red); color: var(--red); }

#   .save-info {
#     font-size: 0.78rem;
#     color: var(--muted);
#     font-family: 'DM Mono', monospace;
#   }

#   /* ── History sidebar ── */
#   .history-section {
#     margin-top: 2.5rem;
#     border-top: 1px solid var(--border);
#     padding-top: 1.5rem;
#   }
#   .history-title {
#     font-size: 0.75rem;
#     font-family: 'DM Mono', monospace;
#     color: var(--muted);
#     text-transform: uppercase;
#     letter-spacing: 0.08em;
#     margin-bottom: 0.75rem;
#   }
#   .history-list {
#     display: flex;
#     flex-wrap: wrap;
#     gap: 8px;
#   }
#   .history-badge {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 6px;
#     padding: 5px 12px;
#     font-family: 'DM Mono', monospace;
#     font-size: 0.75rem;
#     color: var(--text);
#     text-decoration: none;
#     transition: border-color 0.15s, color 0.15s;
#   }
#   .history-badge:hover { border-color: var(--gold); color: var(--gold); }
#   .history-badge .cnt {
#     font-size: 0.65rem;
#     color: var(--muted);
#     margin-left: 6px;
#   }

#   /* ── Stats row ── */
#   .stats-row {
#     display: grid;
#     grid-template-columns: repeat(3, 1fr);
#     gap: 12px;
#     margin-bottom: 1.5rem;
#   }
#   .stat-card {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 10px;
#     padding: 0.75rem 1rem;
#   }
#   .stat-label {
#     font-size: 0.68rem;
#     color: var(--muted);
#     font-family: 'DM Mono', monospace;
#     text-transform: uppercase;
#     letter-spacing: 0.06em;
#     margin-bottom: 4px;
#   }
#   .stat-value {
#     font-size: 1.3rem;
#     font-weight: 600;
#     color: var(--gold);
#     font-family: 'DM Mono', monospace;
#   }

#   @media (max-width: 600px) {
#     .table-header, .veg-row {
#       grid-template-columns: 36px 1fr 130px 100px;
#     }
#     .stats-row { grid-template-columns: 1fr 1fr; }
#   }
# </style>
# </head>
# <body>

# <header>
#   <div class="brand">
#     <div class="brand-dot"></div>
#     <span class="brand-name">LOCALAI TV — ధర నమోదు</span>
#   </div>
#   <span class="header-date" id="live-clock"></span>
# </header>

# <main>

#   {% if message %}
#   <div class="flash {{ message_type }}">
#     {{ '✓' if message_type == 'success' else '✗' }} {{ message }}
#   </div>
#   {% endif %}

#   <!-- Date selector -->
#   <form method="GET" action="/">
#     <div class="date-bar">
#       <label>తేదీ ఎంచుకోండి</label>
#       <input type="date" name="date" value="{{ selected_date }}" id="date-pick">
#       <button type="submit" class="btn-load">Load</button>
#       <span class="save-info" style="margin-left:auto">{{ total_filled }}/{{ vegetables|length }} filled</span>
#     </div>
#   </form>

#   <!-- Stats -->
#   <div class="stats-row">
#     <div class="stat-card">
#       <div class="stat-label">కూరగాయలు</div>
#       <div class="stat-value">{{ vegetables|length }}</div>
#     </div>
#     <div class="stat-card">
#       <div class="stat-label">ధరలు నమోదు</div>
#       <div class="stat-value" id="filled-count">{{ total_filled }}</div>
#     </div>
#     <div class="stat-card">
#       <div class="stat-label">తేదీ</div>
#       <div class="stat-value" style="font-size:0.9rem">{{ selected_date }}</div>
#     </div>
#   </div>

#   <!-- Price entry form -->
#   <form method="POST" action="/save" id="price-form">
#     <input type="hidden" name="price_date" value="{{ selected_date }}">

#     <div class="price-table-wrap">
#       <div class="table-header">
#         <span>S.No</span>
#         <span>కూరగాయ పేరు</span>
#         <span>ధర (Rs. లేదా X/Y)</span>
#         <span>రకం</span>
#       </div>

#       {% for veg in vegetables %}
#       <div class="veg-row">
#         <span class="sno">{{ loop.index }}</span>
#         <span class="veg-name">{{ veg.name }}</span>
#         <input
#           type="text"
#           class="price-input"
#           name="prices[]"
#           value="{{ veg.existing_price }}"
#           placeholder="28  లేదా  5/10"
#           autocomplete="off"
#           oninput="updateCount()"
#         >
#         <input type="hidden" name="names[]" value="{{ veg.name }}">
#         <select class="type-select" name="price_types[]">
#           <option value="per_kg"    {% if veg.price_type == 'per_kg'    %}selected{% endif %}>/kg</option>
#           <option value="per_piece" {% if veg.price_type == 'per_piece' %}selected{% endif %}>pcs</option>
#         </select>
#       </div>
#       {% endfor %}
#     </div>

#     <div class="actions">
#       <button type="submit" class="btn-save">💾 Save</button>
#       <button type="button" class="btn-clear" onclick="clearAll()">Clear All</button>
#       <span class="save-info">Saves to: db/prices.db</span>
#     </div>
#   </form>

#   <!-- History -->
#   {% if history %}
#   <div class="history-section">
#     <div class="history-title">Previous recordings</div>
#     <div class="history-list">
#       {% for h in history %}
#       <a href="/?date={{ h.date }}" class="history-badge">
#         {{ h.date }}<span class="cnt">{{ h.cnt }} items</span>
#       </a>
#       {% endfor %}
#     </div>
#   </div>
#   {% endif %}

# </main>

# <script>
#   // Live clock
#   function tick() {
#     const now = new Date();
#     document.getElementById('live-clock').textContent =
#       now.toLocaleTimeString('te-IN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
#   }
#   tick(); setInterval(tick, 1000);

#   // Filled counter
#   function updateCount() {
#     const inputs = document.querySelectorAll('.price-input');
#     let filled = 0;
#     inputs.forEach(i => { if (i.value.trim()) filled++; });
#     document.getElementById('filled-count').textContent = filled;
#   }

#   // Clear all prices
#   function clearAll() {
#     if (!confirm('అన్ని ధరలు క్లియర్ చేయాలా?')) return;
#     document.querySelectorAll('.price-input').forEach(i => i.value = '');
#     updateCount();
#   }

#   // Auto-select type when X/Y format is typed
#   document.querySelectorAll('.price-input').forEach((inp, idx) => {
#     inp.addEventListener('input', () => {
#       const selects = document.querySelectorAll('.type-select');
#       if (inp.value.includes('/')) {
#         selects[idx].value = 'per_piece';
#       }
#     });
#   });
# </script>
# </body>
# </html>
# """

# # ─────────────────────────────────────────────────────────────────────────────
# # ROUTES
# # ─────────────────────────────────────────────────────────────────────────────

# @app.route("/")
# def index():
#     selected_date = request.args.get("date", date.today().isoformat())
#     message       = request.args.get("msg", "")
#     message_type  = request.args.get("type", "success")

#     master     = load_master_vegetables()
#     existing   = get_existing_prices(selected_date)
#     history    = get_all_dates()

#     vegetables = []
#     for name in master:
#         ex = existing.get(name, {})
#         # Show price_raw if available (preserves X/Y format), else numeric price
#         raw = ex.get("price_raw") or ""
#         if not raw and ex.get("price") is not None:
#             raw = str(int(ex["price"]))
#         vegetables.append({
#             "name":           name,
#             "existing_price": raw,
#             "price_type":     ex.get("price_type", "per_kg"),
#         })

#     total_filled = sum(1 for v in vegetables if v["existing_price"])

#     return render_template_string(
#         HTML,
#         vegetables    = vegetables,
#         selected_date = selected_date,
#         message       = message,
#         message_type  = message_type,
#         history       = history,
#         total_filled  = total_filled,
#     )


# @app.route("/save", methods=["POST"])
# def save():
#     price_date  = request.form.get("price_date", date.today().isoformat())
#     names       = request.form.getlist("names[]")
#     prices      = request.form.getlist("prices[]")
#     price_types = request.form.getlist("price_types[]")

#     if not names:
#         return redirect(url_for("index", msg="No data received.", type="error"))

#     form_data = {"names": names, "prices": prices, "price_types": price_types}
#     saved = save_prices(form_data, price_date)

#     return redirect(url_for(
#         "index",
#         date  = price_date,
#         msg   = f"✓ {saved} vegetables saved for {price_date}",
#         type  = "success"
#     ))


# @app.route("/api/prices/<price_date>")
# def api_prices(price_date):
#     """JSON API — useful for debugging or external access."""
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT sno, name_telugu, price, price_display, price_type, price_raw "
#         "FROM prices WHERE date=? ORDER BY sno",
#         (price_date,)
#     ).fetchall()
#     conn.close()
#     return jsonify([dict(r) for r in rows])


# # ─────────────────────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     import socket
#     hostname = socket.gethostname()
#     try:
#         local_ip = socket.gethostbyname(hostname)
#     except Exception:
#         local_ip = "127.0.0.1"

#     print(f"""
# ╔══════════════════════════════════════════════════════╗
# ║  LocalAI TV — Price Entry Form                       ║
# ╠══════════════════════════════════════════════════════╣
# ║  Local  : http://localhost:5001                      ║
# ║  Network: http://{local_ip:<36}║
# ╠══════════════════════════════════════════════════════╣
# ║  Database : db/prices.db                             ║
# ║  Master   : db/master_vegetables.json                ║
# ║  API      : /api/prices/YYYY-MM-DD                   ║
# ╚══════════════════════════════════════════════════════╝
# """)
#     app.run(debug=False, host="0.0.0.0", port=5001)


























# """
# form_app.py
# ===========
# LocalAI TV — Web Form for Manual Price Entry

# Run:
#     pip install flask
#     python form_app.py

# Then open: http://localhost:5001
# Share on your network: http://<your-ip>:5001
# """

# import sqlite3
# import json
# import re
# from datetime import date, datetime
# from pathlib import Path
# from flask import Flask, render_template_string, request, redirect, url_for, jsonify

# # ── Path config — adjust if running from a different folder ──────────────────
# BASE_DIR        = Path(__file__).parent
# DB_PATH         = BASE_DIR / "db" / "prices.db"
# MASTER_VEG_FILE = BASE_DIR / "db" / "master_vegetables.json"

# app = Flask(__name__)

# # ─────────────────────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────────────────────

# def load_master_vegetables() -> list:
#     if not MASTER_VEG_FILE.exists():
#         return []
#     with open(MASTER_VEG_FILE, encoding="utf-8") as f:
#         data = json.load(f)
#     return data.get("vegetables", [])


# def get_db():
#     DB_PATH.parent.mkdir(parents=True, exist_ok=True)
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     # Ensure table + columns exist
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS prices (
#             id            INTEGER PRIMARY KEY AUTOINCREMENT,
#             date          TEXT NOT NULL,
#             sno           INTEGER,
#             name_telugu   TEXT NOT NULL,
#             price         REAL,
#             price_display TEXT NOT NULL DEFAULT '',
#             grade         TEXT DEFAULT 'I',
#             price_type    TEXT DEFAULT 'per_kg',
#             price_raw     TEXT,
#             created_at    TEXT
#         )
#     """)
#     # Add missing columns to existing DB (safe to call each time)
#     existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(prices)").fetchall()]
#     for col, defn in [
#         ("price_type", "TEXT DEFAULT 'per_kg'"),
#         ("price_raw",  "TEXT"),
#         ("sno",        "INTEGER"),
#         ("price_display", "TEXT NOT NULL DEFAULT ''"),
#     ]:
#         if col not in existing_cols:
#             conn.execute(f"ALTER TABLE prices ADD COLUMN {col} {defn}")
#     conn.commit()
#     return conn


# def is_per_piece(raw) -> bool:
#     if raw is None:
#         return False
#     s = str(raw).strip()
#     parts = s.split("/")
#     if len(parts) == 2:
#         try:
#             float(parts[0].strip())
#             float(parts[1].strip())
#             return True
#         except ValueError:
#             pass
#     return False


# def parse_price(raw):
#     if raw is None or str(raw).strip() in ("", "null", "none"):
#         return None
#     s = str(raw).strip()
#     if "/" in s:
#         parts = s.split("/")
#         try:
#             return float(parts[1].strip())  # store the rate
#         except ValueError:
#             pass
#         s = parts[0].strip()
#     s = re.sub(r"[^\d.]", "", s)
#     try:
#         return float(s) if s else None
#     except ValueError:
#         return None


# def format_price_display(raw, price_type: str) -> str:
#     if not raw or str(raw).strip() in ("", "null"):
#         return "తెలియలేదు"
#     if price_type == "per_piece" and "/" in str(raw):
#         parts = str(raw).split("/")
#         try:
#             count = int(float(parts[0].strip()))
#             rate  = int(float(parts[1].strip()))
#             return f"Pcs {count}/{rate} Rs"
#         except (ValueError, IndexError):
#             pass
#     val = parse_price(raw)
#     return f"Rs.{int(val)}" if val is not None else "తెలియలేదు"


# def get_existing_prices(price_date: str) -> dict:
#     """Return {name_telugu: row} for a given date."""
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT name_telugu, price, price_type, price_raw, sno FROM prices WHERE date=? ORDER BY sno",
#         (price_date,)
#     ).fetchall()
#     conn.close()
#     return {r["name_telugu"]: dict(r) for r in rows}


# def save_prices(form_data: dict, price_date: str) -> int:
#     conn  = get_db()
#     saved = 0

#     # Only process rows where user actually typed a price — collect them first
#     rows_to_save = []
#     for sno, name in enumerate(form_data["names"], 1):
#         raw_price = form_data["prices"][sno - 1].strip()

#         # Skip completely blank fields — don't touch DB for these
#         if not raw_price:
#             continue

#         # Auto-detect type from the value itself — X/Y = per_piece, number = per_kg
#         # The hidden field is a fallback but the value format is authoritative
#         if is_per_piece(raw_price):
#             price_type = "per_piece"
#         else:
#             price_type = "per_kg"

#         rows_to_save.append({
#             "sno":        sno,
#             "name":       name.strip(),
#             "raw_price":  raw_price,
#             "price_type": price_type,
#         })

#     if not rows_to_save:
#         conn.close()
#         return 0

#     # Delete only the specific vegetables that have new values being saved.
#     # Vegetables not submitted stay untouched in the DB.
#     names_being_saved = [r["name"] for r in rows_to_save]
#     placeholders = ",".join("?" * len(names_being_saved))
#     conn.execute(
#         f"DELETE FROM prices WHERE date=? AND name_telugu IN ({placeholders})",
#         [price_date] + names_being_saved
#     )

#     for r in rows_to_save:
#         price_val     = parse_price(r["raw_price"])
#         price_display = format_price_display(r["raw_price"], r["price_type"])
#         conn.execute(
#             """INSERT INTO prices
#                (date, sno, name_telugu, price, price_display, grade, price_type, price_raw, created_at)
#                VALUES (?, ?, ?, ?, ?, 'I', ?, ?, ?)""",
#             (
#                 price_date, r["sno"], r["name"],
#                 price_val, price_display,
#                 r["price_type"], r["raw_price"],
#                 datetime.now().isoformat()
#             )
#         )
#         saved += 1

#     conn.commit()
#     conn.close()
#     return saved


# def get_all_dates():
#     if not DB_PATH.exists():
#         return []
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT date, COUNT(*) as cnt FROM prices GROUP BY date ORDER BY date DESC LIMIT 30"
#     ).fetchall()
#     conn.close()
#     return [dict(r) for r in rows]


# # ─────────────────────────────────────────────────────────────────────────────
# # HTML TEMPLATE
# # ─────────────────────────────────────────────────────────────────────────────

# HTML = """<!DOCTYPE html>
# <html lang="te">
# <head>
# <meta charset="UTF-8">
# <meta name="viewport" content="width=device-width, initial-scale=1.0">
# <title>LocalAI TV — ధర నమోదు</title>
# <link href="https://fonts.googleapis.com/css2?family=Tiro+Telugu&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
# <style>
#   :root {
#     --bg:       #0d1117;
#     --surface:  #161b22;
#     --border:   #30363d;
#     --gold:     #f5c518;
#     --gold-dim: #c49b12;
#     --green:    #3fb950;
#     --red:      #f85149;
#     --text:     #e6edf3;
#     --muted:    #8b949e;
#     --input-bg: #0d1117;
#   }

#   * { box-sizing: border-box; margin: 0; padding: 0; }

#   body {
#     background: var(--bg);
#     color: var(--text);
#     font-family: 'DM Sans', sans-serif;
#     min-height: 100vh;
#   }

#   /* ── Header ── */
#   header {
#     background: var(--surface);
#     border-bottom: 1px solid var(--border);
#     padding: 1rem 1.5rem;
#     display: flex;
#     align-items: center;
#     justify-content: space-between;
#     position: sticky;
#     top: 0;
#     z-index: 100;
#   }
#   .brand { display: flex; align-items: center; gap: 10px; }
#   .brand-dot {
#     width: 10px; height: 10px; border-radius: 50%;
#     background: var(--gold);
#     box-shadow: 0 0 8px var(--gold);
#     animation: pulse 2s ease-in-out infinite;
#   }
#   @keyframes pulse {
#     0%,100% { opacity: 1; } 50% { opacity: 0.4; }
#   }
#   .brand-name {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.85rem;
#     color: var(--gold);
#     letter-spacing: 0.08em;
#     font-weight: 500;
#   }
#   .header-date {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.75rem;
#     color: var(--muted);
#   }

#   /* ── Layout ── */
#   main {
#     max-width: 860px;
#     margin: 0 auto;
#     padding: 2rem 1rem 4rem;
#   }

  


#   /* ── Flash messages ── */
#   .flash {
#     padding: 0.75rem 1rem;
#     border-radius: 8px;
#     margin-bottom: 1rem;
#     font-size: 0.9rem;
#     display: flex;
#     align-items: center;
#     gap: 8px;
#   }
#   .flash.success { background: rgba(63,185,80,0.15); border: 1px solid rgba(63,185,80,0.4); color: var(--green); }
#   .flash.error   { background: rgba(248,81,73,0.15);  border: 1px solid rgba(248,81,73,0.4);  color: var(--red); }

#   /* ── Table ── */
#   .price-table-wrap {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 12px;
#     overflow: hidden;
#     margin-bottom: 1.5rem;
#   }
#   .table-header {
#     display: grid;
#     grid-template-columns: 48px 1fr 160px 120px;
#     gap: 0;
#     background: #1c2128;
#     border-bottom: 1px solid var(--border);
#     padding: 0.6rem 1rem;
#   }
#   .table-header span {
#     font-size: 0.7rem;
#     font-family: 'DM Mono', monospace;
#     color: var(--muted);
#     letter-spacing: 0.06em;
#     text-transform: uppercase;
#   }

#   .veg-row {
#     display: grid;
#     grid-template-columns: 48px 1fr 160px 120px;
#     gap: 0;
#     align-items: center;
#     border-bottom: 1px solid rgba(48,54,61,0.5);
#     padding: 0.4rem 1rem;
#     transition: background 0.1s;
#   }
#   .veg-row:last-child { border-bottom: none; }
#   .veg-row:hover { background: rgba(255,255,255,0.02); }

#   .sno {
#     font-family: 'DM Mono', monospace;
#     font-size: 0.75rem;
#     color: var(--muted);
#   }

#   .veg-name {
#     font-family: 'Tiro Telugu', serif;
#     font-size: 1rem;
#     color: var(--text);
#     padding-right: 12px;
#   }

#   .price-input {
#     background: var(--input-bg);
#     border: 1px solid var(--border);
#     color: var(--text);
#     border-radius: 6px;
#     padding: 7px 10px;
#     font-family: 'DM Mono', monospace;
#     font-size: 0.88rem;
#     width: 100%;
#     transition: border-color 0.15s;
#   }
#   .price-input:focus {
#     outline: none;
#     border-color: var(--gold);
#     box-shadow: 0 0 0 3px rgba(245,197,24,0.1);
#   }
#   .price-input::placeholder { color: #444d56; }

#   .type-badge {
#     display: inline-flex;
#     align-items: center;
#     justify-content: center;
#     margin-left: 8px;
#     padding: 4px 10px;
#     border-radius: 5px;
#     font-size: 0.7rem;
#     font-family: 'DM Mono', monospace;
#     font-weight: 500;
#     letter-spacing: 0.04em;
#     transition: background 0.15s, color 0.15s, border-color 0.15s;
#     pointer-events: none;
#     white-space: nowrap;
#     min-width: 52px;
#     text-align: center;
#   }
#   .type-badge.kg    { background: rgba(63,185,80,0.12);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
#   .type-badge.pcs   { background: rgba(245,197,24,0.12); color: #f5c518; border: 1px solid rgba(245,197,24,0.3); }
#   .type-badge.empty { background: transparent; color: transparent; border: 1px solid transparent; }

#   /* ── Actions ── */
#   .actions {
#     display: flex;
#     gap: 12px;
#     align-items: center;
#   }

#   .btn-save {
#     background: var(--gold);
#     color: #000;
#     border: none;
#     padding: 10px 28px;
#     border-radius: 8px;
#     font-size: 0.9rem;
#     font-weight: 600;
#     cursor: pointer;
#     font-family: 'DM Sans', sans-serif;
#     transition: transform 0.1s, background 0.15s;
#   }
#   .btn-save:hover { background: var(--gold-dim); }
#   .btn-save:active { transform: scale(0.97); }

#   .btn-clear {
#     background: transparent;
#     border: 1px solid var(--border);
#     color: var(--muted);
#     padding: 10px 20px;
#     border-radius: 8px;
#     font-size: 0.85rem;
#     cursor: pointer;
#     font-family: 'DM Sans', sans-serif;
#     transition: border-color 0.15s, color 0.15s;
#   }
#   .btn-clear:hover { border-color: var(--red); color: var(--red); }

#   .save-info {
#     font-size: 0.78rem;
#     color: var(--muted);
#     font-family: 'DM Mono', monospace;
#   }



#   /* ── Stats row ── */
#   .stats-row {
#     display: grid;
#     grid-template-columns: repeat(3, 1fr);
#     gap: 12px;
#     margin-bottom: 1.5rem;
#   }
#   .stat-card {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 10px;
#     padding: 0.75rem 1rem;
#   }
#   .stat-label {
#     font-size: 0.68rem;
#     color: var(--muted);
#     font-family: 'DM Mono', monospace;
#     text-transform: uppercase;
#     letter-spacing: 0.06em;
#     margin-bottom: 4px;
#   }
#   .stat-value {
#     font-size: 1.3rem;
#     font-weight: 600;
#     color: var(--gold);
#     font-family: 'DM Mono', monospace;
#   }

#   @media (max-width: 600px) {
#     .table-header, .veg-row {
#       grid-template-columns: 36px 1fr 130px 100px;
#     }
#     .stats-row { grid-template-columns: 1fr 1fr; }
#   }
# </style>
# </head>
# <body>

# <header>
#   <div class="brand">
#     <div class="brand-dot"></div>
#     <span class="brand-name">LOCALAI TV — ధర నమోదు</span>
#   </div>
#   <span class="header-date" id="live-clock"></span>
# </header>

# <main>

#   {% if message %}
#   <div class="flash {{ message_type }}">
#     {{ '✓' if message_type == 'success' else '✗' }} {{ message }}
#   </div>
#   {% endif %}

 

#   <!-- Stats -->
#   <div class="stats-row">
#     <div class="stat-card">
#       <div class="stat-label">కూరగాయలు</div>
#       <div class="stat-value">{{ vegetables|length }}</div>
#     </div>
#     <div class="stat-card">
#       <div class="stat-label">ధరలు నమోదు</div>
#       <div class="stat-value" id="filled-count">{{ total_filled }}</div>
#     </div>
#     <div class="stat-card">
#       <div class="stat-label">తేదీ</div>
#       <div class="stat-value" style="font-size:0.9rem">{{ selected_date }}</div>
#     </div>
#   </div>

#   <!-- Price entry form -->
#   <form method="POST" action="/save" id="price-form">
#     <input type="hidden" name="price_date" value="{{ selected_date }}">

#     <div class="price-table-wrap">
#       <div class="table-header">
#         <span>S.No</span>
#         <span>కూరగాయ పేరు</span>
#         <span>ధర (Rs. లేదా X/Y)</span>
#         <span>Auto</span>
#       </div>

#       {% for veg in vegetables %}
#       <div class="veg-row">
#         <span class="sno">{{ loop.index }}</span>
#         <span class="veg-name">{{ veg.name }}</span>
#         <input
#           type="text"
#           class="price-input"
#           name="prices[]"
#           value="{{ veg.existing_price }}"
#           placeholder="28  లేదా  5/10"
#           autocomplete="off"
#           oninput="autoDetectType(this); updateCount()"
#         >
#         <input type="hidden" name="names[]" value="{{ veg.name }}">
#         <input type="hidden" class="type-hidden" name="price_types[]"
#                value="{{ veg.price_type }}">
#         <span class="type-badge {% if veg.existing_price %}{% if veg.price_type == 'per_piece' %}pcs{% else %}kg{% endif %}{% else %}empty{% endif %}">
#           {% if veg.existing_price %}{% if veg.price_type == 'per_piece' %}pcs{% else %}/kg{% endif %}{% endif %}
#         </span>
#       </div>
#       {% endfor %}
#     </div>

#     <div class="actions">
#       <button type="submit" class="btn-save">💾 Save to Database</button>
#       <button type="button" class="btn-clear" onclick="clearAll()">Clear All</button>
#       <span class="save-info">Saves to: db/prices.db</span>
#     </div>
#   </form>



# </main>

# <script>
#   // Live clock
#   function tick() {
#   const now = new Date();
#   document.getElementById('live-clock').textContent =
#     now.toLocaleTimeString('te-IN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
# }
# tick(); setInterval(tick, 1000);

# // Auto-fill today's date in the date input field
# window.addEventListener('DOMContentLoaded', () => {
#   const dateInput = document.querySelector('input[type="date"][name="goto_date"]');
#   if (dateInput && !dateInput.value) {
#     const today = new Date().toISOString().split('T')[0];
#     dateInput.value = today;
#   }
# });


#   // Filled counter
#   function updateCount() {
#     const inputs = document.querySelectorAll('.price-input');
#     let filled = 0;
#     inputs.forEach(i => { if (i.value.trim()) filled++; });
#     document.getElementById('filled-count').textContent = filled;
#   }

#   // Toggle the date override panel
#   function toggleDatePicker() {
#     const panel = document.getElementById('date-override-panel');
#     const btn   = document.querySelector('.btn-change-date');
#     const open  = panel.style.display === 'none';
#     panel.style.display = open ? 'block' : 'none';
#     btn.textContent = open ? 'వేరే తేదీ ▴' : 'వేరే తేదీ ▾';
#   }

#   // Auto open picker if viewing a past date
#   {% if not is_today %}
#   window.addEventListener('DOMContentLoaded', () => {
#     document.getElementById('date-override-panel').style.display = 'block';
#     document.querySelector('.btn-change-date').textContent = 'వేరే తేదీ ▴';
#   });
#   {% endif %}

#   // Clear all prices
#   function clearAll() {
#     if (!confirm('అన్ని ధరలు క్లియర్ చేయాలా?')) return;
#     document.querySelectorAll('.price-input').forEach(i => i.value = '');
#     updateCount();
#   }

#   // Auto-detect price type from value — no manual selection needed
#   function autoDetectType(inp) {
#     const row    = inp.closest('.veg-row');
#     const hidden = row.querySelector('.type-hidden');
#     const badge  = row.querySelector('.type-badge');
#     const val    = inp.value.trim();

#     if (!val) {
#       hidden.value = 'per_kg';
#       badge.className = 'type-badge empty';
#       badge.textContent = '';
#       return;
#     }

#     // X/Y pattern = per_piece (e.g. 5/10, 6/8, 12/20)
#     const isPiece = /^\d+(\.\d+)?\s*\/\s*\d+(\.\d+)?$/.test(val);
#     if (isPiece) {
#       hidden.value = 'per_piece';
#       badge.className = 'type-badge pcs';
#       badge.textContent = 'pcs';
#     } else {
#       hidden.value = 'per_kg';
#       badge.className = 'type-badge kg';
#       badge.textContent = '/kg';
#     }
#   }

#   // Run auto-detect on page load for pre-filled values
#   document.querySelectorAll('.price-input').forEach(inp => autoDetectType(inp));
# </script>
# </body>
# </html>
# """

# # ─────────────────────────────────────────────────────────────────────────────
# # ROUTES
# # ─────────────────────────────────────────────────────────────────────────────

# @app.route("/")
# def index():
#     selected_date = request.args.get("date", date.today().isoformat())
#     message       = request.args.get("msg", "")
#     message_type  = request.args.get("type", "success")

#     master     = load_master_vegetables()
#     existing   = get_existing_prices(selected_date)
#     history    = get_all_dates()

#     vegetables = []
#     for name in master:
#         ex = existing.get(name, {})
#         # Show price_raw if available (preserves X/Y format), else numeric price
#         raw = ex.get("price_raw") or ""
#         if not raw and ex.get("price") is not None:
#             raw = str(int(ex["price"]))
#         vegetables.append({
#             "name":           name,
#             "existing_price": raw,
#             "price_type":     ex.get("price_type", "per_kg"),
#         })

#     total_filled = sum(1 for v in vegetables if v["existing_price"])

#     return render_template_string(
#         HTML,
#         vegetables    = vegetables,
#         selected_date = selected_date,
#         message       = message,
#         message_type  = message_type,
#         history       = history,
#         total_filled  = total_filled,
#     )


# @app.route("/save", methods=["POST"])
# def save():
#     price_date  = request.form.get("price_date", date.today().isoformat())
#     names       = request.form.getlist("names[]")
#     prices      = request.form.getlist("prices[]")
#     price_types = request.form.getlist("price_types[]")

#     if not names:
#         return redirect(url_for("index", msg="No data received.", type="error"))

#     form_data = {"names": names, "prices": prices, "price_types": price_types}
#     saved = save_prices(form_data, price_date)

#     return redirect(url_for(
#         "index",
#         date  = price_date,
#         msg   = f"✓ {saved} vegetables saved for {price_date}",
#         type  = "success"
#     ))


# @app.route("/api/prices/<price_date>")
# def api_prices(price_date):
#     """JSON API — useful for debugging or external access."""
#     conn = get_db()
#     rows = conn.execute(
#         "SELECT sno, name_telugu, price, price_display, price_type, price_raw "
#         "FROM prices WHERE date=? ORDER BY sno",
#         (price_date,)
#     ).fetchall()
#     conn.close()
#     return jsonify([dict(r) for r in rows])


# # ─────────────────────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     import socket
#     hostname = socket.gethostname()
#     try:
#         local_ip = socket.gethostbyname(hostname)
#     except Exception:
#         local_ip = "127.0.0.1"

#     print(f"""
# ╔══════════════════════════════════════════════════════╗
# ║  LocalAI TV — Price Entry Form                       ║
# ╠══════════════════════════════════════════════════════╣
# ║  Local  : http://localhost:5001                      ║
# ║  Network: http://{local_ip:<36}║
# ╠══════════════════════════════════════════════════════╣
# ║  Database : db/prices.db                             ║
# ║  Master   : db/master_vegetables.json                ║
# ║  API      : /api/prices/YYYY-MM-DD                   ║
# ╚══════════════════════════════════════════════════════╝
# """)
#     app.run(debug=False, host="0.0.0.0", port=5001)



















"""
form_app.py
===========
LocalAI TV — Web Form for Manual Price Entry

Run:
    pip install flask
    python form_app.py

Then open: http://localhost:5001
Share on your network: http://<your-ip>:5001
"""

import sqlite3
import json
import re
from datetime import date, datetime
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

# ── Path config — adjust if running from a different folder ──────────────────
BASE_DIR        = Path(__file__).parent
DB_PATH         = BASE_DIR / "db" / "prices.db"
MASTER_VEG_FILE = BASE_DIR / "db" / "master_vegetables.json"

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_master_vegetables() -> list:
    if not MASTER_VEG_FILE.exists():
        return []
    with open(MASTER_VEG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("vegetables", [])


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date          TEXT NOT NULL,
            sno           INTEGER,
            name_telugu   TEXT NOT NULL,
            price         REAL,
            price_display TEXT NOT NULL DEFAULT '',
            grade         TEXT DEFAULT 'I',
            price_type    TEXT DEFAULT 'per_kg',
            price_raw     TEXT,
            created_at    TEXT
        )
    """)
    existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(prices)").fetchall()]
    for col, defn in [
        ("price_type",    "TEXT DEFAULT 'per_kg'"),
        ("price_raw",     "TEXT"),
        ("sno",           "INTEGER"),
        ("price_display", "TEXT NOT NULL DEFAULT ''"),
    ]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE prices ADD COLUMN {col} {defn}")
    conn.commit()
    return conn


def is_per_piece(raw) -> bool:
    if raw is None:
        return False
    s = str(raw).strip()
    parts = s.split("/")
    if len(parts) == 2:
        try:
            float(parts[0].strip())
            float(parts[1].strip())
            return True
        except ValueError:
            pass
    return False


def parse_price(raw):
    if raw is None or str(raw).strip() in ("", "null", "none"):
        return None
    s = str(raw).strip()
    if "/" in s:
        parts = s.split("/")
        try:
            return float(parts[1].strip())
        except ValueError:
            pass
        s = parts[0].strip()
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else None
    except ValueError:
        return None


def format_price_display(raw, price_type: str) -> str:
    if not raw or str(raw).strip() in ("", "null"):
        return "తెలియలేదు"
    if price_type == "per_piece" and "/" in str(raw):
        parts = str(raw).split("/")
        try:
            count = int(float(parts[0].strip()))
            rate  = int(float(parts[1].strip()))
            return f"Pcs {count}/{rate} Rs"
        except (ValueError, IndexError):
            pass
    val = parse_price(raw)
    return f"Rs.{int(val)}" if val is not None else "తెలియలేదు"


def get_existing_prices(price_date: str) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT name_telugu, price, price_type, price_raw, sno FROM prices WHERE date=? ORDER BY sno",
        (price_date,)
    ).fetchall()
    conn.close()
    return {r["name_telugu"]: dict(r) for r in rows}


def save_prices(form_data: dict, price_date: str) -> int:
    conn = get_db()

    rows_to_save = []
    for sno, name in enumerate(form_data["names"], 1):
        raw_price = form_data["prices"][sno - 1].strip()
        if not raw_price:
            continue
        price_type = "per_piece" if is_per_piece(raw_price) else "per_kg"
        rows_to_save.append({
            "sno":        sno,
            "name":       name.strip(),
            "raw_price":  raw_price,
            "price_type": price_type,
        })

    if not rows_to_save:
        conn.close()
        return 0

    names_being_saved = [r["name"] for r in rows_to_save]
    placeholders = ",".join("?" * len(names_being_saved))
    conn.execute(
        f"DELETE FROM prices WHERE date=? AND name_telugu IN ({placeholders})",
        [price_date] + names_being_saved
    )

    for r in rows_to_save:
        price_val     = parse_price(r["raw_price"])
        price_display = format_price_display(r["raw_price"], r["price_type"])
        conn.execute(
            """INSERT INTO prices
               (date, sno, name_telugu, price, price_display, grade, price_type, price_raw, created_at)
               VALUES (?, ?, ?, ?, ?, 'I', ?, ?, ?)""",
            (
                price_date, r["sno"], r["name"],
                price_val, price_display,
                r["price_type"], r["raw_price"],
                datetime.now().isoformat()
            )
        )

    conn.commit()
    conn.close()
    return len(rows_to_save)


# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LocalAI TV — ధర నమోదు</title>
<link href="https://fonts.googleapis.com/css2?family=Tiro+Telugu&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #0d1117;
    --surface:  #161b22;
    --border:   #30363d;
    --gold:     #f5c518;
    --gold-dim: #c49b12;
    --green:    #3fb950;
    --red:      #f85149;
    --text:     #e6edf3;
    --muted:    #8b949e;
    --input-bg: #0d1117;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .brand { display: flex; align-items: center; gap: 10px; }
  .brand-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--gold);
    box-shadow: 0 0 8px var(--gold);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%,100% { opacity: 1; } 50% { opacity: 0.4; }
  }
  .brand-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: var(--gold);
    letter-spacing: 0.08em;
    font-weight: 500;
  }
  .header-date {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
  }

  /* ── Layout ── */
  main {
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1rem 4rem;
  }

  /* ── Flash messages ── */
  .flash {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .flash.success { background: rgba(63,185,80,0.15); border: 1px solid rgba(63,185,80,0.4); color: var(--green); }
  .flash.error   { background: rgba(248,81,73,0.15);  border: 1px solid rgba(248,81,73,0.4);  color: var(--red); }

  /* ── Table ── */
  .price-table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }
  .table-header {
    display: grid;
    grid-template-columns: 48px 1fr 160px 120px;
    gap: 0;
    background: #1c2128;
    border-bottom: 1px solid var(--border);
    padding: 0.6rem 1rem;
  }
  .table-header span {
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .veg-row {
    display: grid;
    grid-template-columns: 48px 1fr 160px 120px;
    gap: 0;
    align-items: center;
    border-bottom: 1px solid rgba(48,54,61,0.5);
    padding: 0.4rem 1rem;
    transition: background 0.1s;
  }
  .veg-row:last-child { border-bottom: none; }
  .veg-row:hover { background: rgba(255,255,255,0.02); }

  .sno {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
  }

  .veg-name {
    font-family: 'Tiro Telugu', serif;
    font-size: 1rem;
    color: var(--text);
    padding-right: 12px;
  }

  .price-input {
    background: var(--input-bg);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    padding: 7px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    width: 100%;
    transition: border-color 0.15s;
  }
  .price-input:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(245,197,24,0.1);
  }
  .price-input::placeholder { color: #444d56; }

  .type-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-left: 8px;
    padding: 4px 10px;
    border-radius: 5px;
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.04em;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    pointer-events: none;
    white-space: nowrap;
    min-width: 52px;
    text-align: center;
  }
  .type-badge.kg    { background: rgba(63,185,80,0.12);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
  .type-badge.pcs   { background: rgba(245,197,24,0.12); color: #f5c518; border: 1px solid rgba(245,197,24,0.3); }
  .type-badge.empty { background: transparent; color: transparent; border: 1px solid transparent; }

  /* ── Actions ── */
  .actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .btn-save {
    background: var(--gold);
    color: #000;
    border: none;
    padding: 10px 28px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    transition: transform 0.1s, background 0.15s;
  }
  .btn-save:hover { background: var(--gold-dim); }
  .btn-save:active { transform: scale(0.97); }

  .btn-clear {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-clear:hover { border-color: var(--red); color: var(--red); }

  .save-info {
    font-size: 0.78rem;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
  }

  /* ── Stats row ── */
  .stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 1rem;
  }
  .stat-label {
    font-size: 0.68rem;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
  }
  .stat-value {
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--gold);
    font-family: 'DM Mono', monospace;
  }

  @media (max-width: 600px) {
    .table-header, .veg-row {
      grid-template-columns: 36px 1fr 130px 100px;
    }
    .stats-row { grid-template-columns: 1fr 1fr; }
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="brand-dot"></div>
    <span class="brand-name">LOCALAI TV — ధర నమోదు</span>
  </div>
  <span class="header-date" id="live-clock"></span>
</header>

<main>

  {% if message %}
  <div class="flash {{ message_type }}">
    {{ '✓' if message_type == 'success' else '✗' }} {{ message }}
  </div>
  {% endif %}

  <!-- Stats -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-label">కూరగాయలు</div>
      <div class="stat-value">{{ vegetables|length }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">ధరలు నమోదు</div>
      <div class="stat-value" id="filled-count">{{ total_filled }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">తేదీ</div>
      <div class="stat-value" style="font-size:0.9rem">{{ selected_date }}</div>
    </div>
  </div>

  <!-- Price entry form -->
  <form method="POST" action="/save" id="price-form">
    <input type="hidden" name="price_date" value="{{ selected_date }}">

    <div class="price-table-wrap">
      <div class="table-header">
        <span>S.No</span>
        <span>కూరగాయ పేరు</span>
        <span>ధర (Rs. లేదా X/Y)</span>
        <span>Auto</span>
      </div>

      {% for veg in vegetables %}
      <div class="veg-row">
        <span class="sno">{{ loop.index }}</span>
        <span class="veg-name">{{ veg.name }}</span>
        <input
          type="text"
          class="price-input"
          name="prices[]"
          value="{{ veg.existing_price }}"
          placeholder="28  లేదా  5/10"
          autocomplete="off"
          oninput="autoDetectType(this); updateCount()"
        >
        <input type="hidden" name="names[]" value="{{ veg.name }}">
        <input type="hidden" class="type-hidden" name="price_types[]"
               value="{{ veg.price_type }}">
        <span class="type-badge {% if veg.existing_price %}{% if veg.price_type == 'per_piece' %}pcs{% else %}kg{% endif %}{% else %}empty{% endif %}">
          {% if veg.existing_price %}{% if veg.price_type == 'per_piece' %}pcs{% else %}/kg{% endif %}{% endif %}
        </span>
      </div>
      {% endfor %}
    </div>

    <div class="actions">
      <button type="submit" class="btn-save">💾 Save </button>
      <button type="button" class="btn-clear" onclick="clearAll()">Clear All</button>
      <span class="save-info"> </span>
    </div>
  </form>

</main>

<script>
  // Live clock
  function tick() {
    const now = new Date();
    document.getElementById('live-clock').textContent =
      now.toLocaleTimeString('te-IN', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
  }
  tick();
  setInterval(tick, 1000);

  // Filled counter
  function updateCount() {
    const inputs = document.querySelectorAll('.price-input');
    let filled = 0;
    inputs.forEach(i => { if (i.value.trim()) filled++; });
    document.getElementById('filled-count').textContent = filled;
  }

  // Clear all prices
  function clearAll() {
    if (!confirm('అన్ని ధరలు క్లియర్ చేయాలా?')) return;
    document.querySelectorAll('.price-input').forEach(i => i.value = '');
    updateCount();
  }

  // Auto-detect price type from value — no manual selection needed
  function autoDetectType(inp) {
    const row    = inp.closest('.veg-row');
    const hidden = row.querySelector('.type-hidden');
    const badge  = row.querySelector('.type-badge');
    const val    = inp.value.trim();

    if (!val) {
      hidden.value = 'per_kg';
      badge.className = 'type-badge empty';
      badge.textContent = '';
      return;
    }

    // X/Y pattern = per_piece (e.g. 5/10, 6/8, 12/20)
    const isPiece = /^\d+(\.\d+)?\s*\/\s*\d+(\.\d+)?$/.test(val);
    if (isPiece) {
      hidden.value = 'per_piece';
      badge.className = 'type-badge pcs';
      badge.textContent = 'pcs';
    } else {
      hidden.value = 'per_kg';
      badge.className = 'type-badge kg';
      badge.textContent = '/kg';
    }
  }

  // Run auto-detect on page load for pre-filled values
  document.querySelectorAll('.price-input').forEach(inp => autoDetectType(inp));
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    selected_date = request.args.get("date", date.today().isoformat())
    message       = request.args.get("msg", "")
    message_type  = request.args.get("type", "success")

    master   = load_master_vegetables()
    existing = get_existing_prices(selected_date)

    vegetables = []
    for name in master:
        ex  = existing.get(name, {})
        raw = ex.get("price_raw") or ""
        if not raw and ex.get("price") is not None:
            raw = str(int(ex["price"]))
        vegetables.append({
            "name":           name,
            "existing_price": raw,
            "price_type":     ex.get("price_type", "per_kg"),
        })

    total_filled = sum(1 for v in vegetables if v["existing_price"])

    return render_template_string(
        HTML,
        vegetables    = vegetables,
        selected_date = selected_date,
        message       = message,
        message_type  = message_type,
        total_filled  = total_filled,
    )


@app.route("/save", methods=["POST"])
def save():
    price_date  = request.form.get("price_date", date.today().isoformat())
    names       = request.form.getlist("names[]")
    prices      = request.form.getlist("prices[]")
    price_types = request.form.getlist("price_types[]")

    if not names:
        return redirect(url_for("index", msg="No data received.", type="error"))

    form_data = {"names": names, "prices": prices, "price_types": price_types}
    saved = save_prices(form_data, price_date)

    return redirect(url_for(
        "index",
        date = price_date,
        msg  = f"✓ {saved} vegetables saved for {price_date}",
        type = "success"
    ))


@app.route("/api/prices/<price_date>")
def api_prices(price_date):
    """JSON API — useful for debugging or external access."""
    conn = get_db()
    rows = conn.execute(
        "SELECT sno, name_telugu, price, price_display, price_type, price_raw "
        "FROM prices WHERE date=? ORDER BY sno",
        (price_date,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    print(f"""
╔══════════════════════════════════════════════════════╗
║  LocalAI TV — Price Entry Form                       ║
╠══════════════════════════════════════════════════════╣
║  Local  : http://localhost:5001                      ║
║  Network: http://{local_ip:<36}║
╠══════════════════════════════════════════════════════╣
║  Database : db/prices.db                             ║
║  Master   : db/master_vegetables.json                ║
║  API      : /api/prices/YYYY-MM-DD                   ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(debug=False, host="0.0.0.0", port=5001)