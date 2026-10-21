"""Small Monero stagenet block explorer for ThothOS (Python standard library only).

Reads the node over its RPC (DAEMON, default http://monerod:38081) and serves http://<phone>:8081.
Pages: / (network + latest blocks + mempool), /block/<height|hash>, /tx/<hash>, /search?q=...
"""
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DAEMON = os.environ.get("DAEMON", "http://monerod:38081").rstrip("/")
PORT = int(os.environ.get("PORT", "8081"))
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
ATOMIC = 1e12


class RpcError(Exception):
    pass


def post(path, payload):
    req = urllib.request.Request(DAEMON + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise RpcError(f"node not reachable ({e})") from e


def rpc(method, params=None):
    r = post("/json_rpc", {"jsonrpc": "2.0", "id": 0, "method": method, "params": params or {}})
    if "error" in r:
        raise RpcError(r["error"].get("message", "rpc error"))
    return r["result"]


def e(v):
    return html.escape(str(v), quote=True)


def xmr(atomic):
    return f"{atomic / ATOMIC:.6f}"


def ago(ts):
    s = int(time.time() - ts)
    if s < 120:
        return f"{s}s ago"
    if s < 7200:
        return f"{s // 60} min ago"
    if s < 172800:
        return f"{s // 3600} h ago"
    return f"{s // 86400} d ago"


def short(h):
    return f"{h[:10]}…{h[-6:]}"


CSS = """
:root{--bg:#07080b;--card:#11141b;--line:#232836;--fg:#e9e6dd;--dim:#8d93a3;--gold:#d8a94a;--blue:#3aa0ff;--ok:#3ecf8e;--bad:#ff6b6b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:18px 16px 10px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header a.brand{color:var(--fg);text-decoration:none;font-weight:600;letter-spacing:.32em}header a.brand b{color:var(--gold)}
.tag{font-size:12px;color:var(--blue);border:1px solid var(--blue);border-radius:99px;padding:1px 8px}
form{margin-left:auto;display:flex;gap:6px;flex:1 1 260px;max-width:520px}
input{flex:1;min-width:0;background:var(--card);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 11px}
button{background:var(--gold);color:#111;border:0;border-radius:8px;padding:9px 14px;font-weight:600}
main{padding:16px;max-width:1100px;margin:auto}h2{font-size:15px;color:var(--gold);font-weight:600;margin:22px 0 8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.stat span{display:block;color:var(--dim);font-size:12px}.stat b{font-size:17px;font-weight:600;word-break:break-all}
.table{overflow-x:auto;border:1px solid var(--line);border-radius:10px}table{border-collapse:collapse;width:100%;min-width:520px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}th{color:var(--dim);font-weight:500;font-size:12px}
tr:last-child td{border-bottom:0}a{color:var(--blue);text-decoration:none}.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px}
.kv{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:4px 12px}.kv div{display:flex;gap:12px;padding:7px 0;border-bottom:1px solid var(--line)}
.kv div:last-child{border:0}.kv span{color:var(--dim);min-width:130px}.kv b{font-weight:500;word-break:break-all}
.ok{color:var(--ok)}.bad{color:var(--bad)}.dim{color:var(--dim)}footer{color:var(--dim);font-size:12px;text-align:center;padding:24px}
"""


def page(title, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · ThothOS stagenet explorer</title>
<style>{CSS}</style></head><body><header><a class="brand" href="/">THOTH<b>OS</b></a><span class="tag">Monero stagenet</span>
<form action="/search"><input name="q" placeholder="block height, block hash or tx hash" aria-label="search">
<button>Search</button></form></header><main>{body}</main>
<footer>Data from your own node · stagenet coins have no value</footer></body></html>"""


def kv(rows):
    return '<div class="kv">' + "".join(f"<div><span>{e(k)}</span><b>{v}</b></div>" for k, v in rows) + "</div>"


def home():
    info = rpc("get_info")
    height = info["height"]
    start = max(0, height - 20)
    headers = rpc("get_block_headers_range", {"start_height": start, "end_height": height - 1})["headers"]
    try:
        pool = post("/get_transaction_pool", {}).get("transactions", [])
    except RpcError:
        pool = None                     # a restricted (public) RPC refuses the pool listing; the rest still works
    synced = info.get("synchronized")
    diff = info.get("difficulty", 0)
    stats = [("Height", f"{height:,}"), ("Sync", '<span class="ok">synchronized</span>' if synced else
             f'<span class="bad">syncing to {info.get("target_height", 0):,}</span>'),
             ("Difficulty", f"{diff:,}"), ("Network hashrate", f"{diff / 120:,.0f} H/s"),
             ("Mempool", f'{info.get("tx_pool_size", len(pool or []))} tx'), ("Peers", f'{info.get("outgoing_connections_count", 0)} out / {info.get("incoming_connections_count", 0)} in'),
             ("Node version", e(info.get("version", "?")))]
    grid = '<div class="grid">' + "".join(f'<div class="stat"><span>{k}</span><b>{v}</b></div>' for k, v in stats) + "</div>"
    rows = "".join(
        f'<tr><td><a href="/block/{h["height"]}">{h["height"]:,}</a></td><td class="dim">{ago(h["timestamp"])}</td>'
        f'<td>{h["num_txes"]}</td><td>{xmr(h["reward"])}</td><td>{h["block_size"] / 1024:.1f} kB</td>'
        f'<td class="mono"><a href="/block/{e(h["hash"])}">{short(h["hash"])}</a></td></tr>'
        for h in reversed(headers))
    blocks = ('<div class="table"><table><tr><th>Height</th><th>Age</th><th>Txs</th><th>Reward XMR</th><th>Size</th>'
              f"<th>Hash</th></tr>{rows}</table></div>")
    prow = "".join(f'<tr><td class="mono"><a href="/tx/{e(t["id_hash"])}">{short(t["id_hash"])}</a></td>'
                   f'<td>{xmr(t.get("fee", 0))}</td><td>{t.get("blob_size", 0) / 1024:.1f} kB</td>'
                   f'<td class="dim">{ago(t.get("receive_time", time.time()))}</td></tr>' for t in (pool or [])[:25])
    if pool is None:
        mem = '<p class="dim">This node does not list its mempool (restricted RPC).</p>'
    elif pool:
        mem = ('<div class="table"><table><tr><th>Tx</th><th>Fee XMR</th><th>Size</th><th>Seen</th></tr>' + prow + "</table></div>")
    else:
        mem = '<p class="dim">Mempool is empty.</p>'
    return page("Overview", f"<h2>Network</h2>{grid}<h2>Latest blocks</h2>{blocks}<h2>Mempool</h2>{mem}")


def block(ident):
    params = {"height": int(ident)} if ident.isdigit() else {"hash": ident}
    b = rpc("get_block", params)
    h = b["block_header"]
    txs = [b.get("miner_tx_hash", "")] + b.get("tx_hashes", [])
    nav = (f'<a href="/block/{h["height"] - 1}">← {h["height"] - 1:,}</a>' if h["height"] > 0 else "") + \
          f' &nbsp; <a href="/block/{h["height"] + 1}">{h["height"] + 1:,} →</a>'
    info = kv([("Height", f'{h["height"]:,}'), ("Hash", f'<span class="mono">{e(h["hash"])}</span>'),
               ("Previous", f'<a class="mono" href="/block/{e(h["prev_hash"])}">{e(h["prev_hash"])}</a>'),
               ("Time", f'{time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(h["timestamp"]))} ({ago(h["timestamp"])})'),
               ("Reward", f'{xmr(h["reward"])} XMR'), ("Difficulty", f'{h["difficulty"]:,}'),
               ("Size", f'{h["block_size"]:,} bytes'), ("Confirmations", f'{h.get("depth", 0):,}'),
               ("Nonce", e(h["nonce"])), ("Orphan", "yes" if h.get("orphan_status") else "no")])
    rows = "".join(f'<tr><td>{"coinbase" if i == 0 else i}</td><td class="mono"><a href="/tx/{e(t)}">{e(t)}</a></td></tr>'
                   for i, t in enumerate(txs) if t)
    return page(f'Block {h["height"]}', f'<h2>Block {h["height"]:,}</h2><p>{nav}</p>{info}<h2>Transactions ({len(txs)})</h2>'
                f'<div class="table"><table><tr><th>#</th><th>Hash</th></tr>{rows}</table></div>')


def tx(txid):
    r = post("/get_transactions", {"txs_hashes": [txid], "decode_as_json": True})
    if not r.get("txs"):
        raise RpcError("transaction not found")
    t = r["txs"][0]
    d = json.loads(t.get("as_json") or "{}")
    vin = d.get("vin", [])
    coinbase = bool(vin) and "gen" in vin[0]
    outs = d.get("vout", [])
    fee = d.get("rct_signatures", {}).get("txnFee", 0)
    where = ('<span class="bad">in mempool</span>' if t.get("in_pool") else
             f'<a href="/block/{t["block_height"]}">{t["block_height"]:,}</a>')
    info = kv([("Hash", f'<span class="mono">{e(txid)}</span>'), ("Block", where),
               ("Type", "coinbase (mined block reward)" if coinbase else "transfer"),
               ("Inputs", "—" if coinbase else str(len(vin))), ("Outputs", str(len(outs))),
               ("Fee", f"{xmr(fee)} XMR" if not coinbase else "—"),
               ("Unlock time", e(d.get("unlock_time", 0))), ("Version", e(d.get("version", "?")))])
    amounts = "".join(f'<tr><td>{i}</td><td>{xmr(o.get("amount", 0)) if o.get("amount") else "hidden (RingCT)"}</td>'
                      f'<td class="mono">{e(outkey(o))}</td></tr>'
                      for i, o in enumerate(outs))
    return page("Transaction", f"<h2>Transaction</h2>{info}<h2>Outputs</h2>"
                f'<div class="table"><table><tr><th>#</th><th>Amount XMR</th><th>One-time key</th></tr>{amounts}</table></div>')


def outkey(o):
    """One-time output key: {"tagged_key": {"key": ..}} since v15, {"key": ".."} before."""
    t = o.get("target") if isinstance(o.get("target"), dict) else {}
    k = t.get("tagged_key", {}).get("key") if isinstance(t.get("tagged_key"), dict) else t.get("key")
    return short(k) if isinstance(k, str) and len(k) > 16 else "—"


def search(q):
    q = q.strip()
    if q.isdigit():
        return ("redirect", f"/block/{int(q)}")
    if HEX64.match(q):
        try:
            rpc("get_block_header_by_hash", {"hash": q})
            return ("redirect", f"/block/{q.lower()}")
        except RpcError:
            return ("redirect", f"/tx/{q.lower()}")
    raise RpcError("enter a block height, a block hash or a transaction hash (64 hex characters)")


class Handler(BaseHTTPRequestHandler):
    server_version = "ThothOS-explorer"

    def send(self, code, body, ctype="text/html; charset=utf-8", location=None):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        if location:
            self.send_header("Location", location)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        try:
            if not parts:
                return self.send(200, home())
            if parts[0] == "block" and len(parts) == 2 and (parts[1].isdigit() or HEX64.match(parts[1])):
                return self.send(200, block(parts[1]))
            if parts[0] == "tx" and len(parts) == 2 and HEX64.match(parts[1]):
                return self.send(200, tx(parts[1].lower()))
            if parts[0] == "search":
                _, loc = search(parse_qs(u.query).get("q", [""])[0])
                return self.send(303, "", location=loc)
            if parts[0] == "health":
                rpc("get_info")
                return self.send(200, "ok", "text/plain")
            return self.send(404, page("Not found", '<h2>Not found</h2><p><a href="/">Back to overview</a></p>'))
        except RpcError as err:
            return self.send(502, page("Error", f'<h2>Could not load</h2><p class="bad">{e(err)}</p><p><a href="/">Overview</a></p>'))

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"explorer on :{PORT}, node {DAEMON}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
