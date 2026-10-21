<h1 align="center">🧪 docker-monero-stagenet</h1>

<p align="center">
  <b>A complete Monero <u>stagenet</u> node in one command, with monitoring, peer map, block explorer and private transaction relay over Tor and i2p.</b><br>
  Stagenet coins have no value, so it's a safe place to learn, test wallets and apps, and try solo mining.
</p>

<p align="center">
  <img alt="Monero" src="https://img.shields.io/badge/Monero-v0.18.5.4-ff6600?logo=monero&logoColor=white">
  <img alt="Network" src="https://img.shields.io/badge/network-stagenet-8250df">
  <img alt="Arch" src="https://img.shields.io/badge/arch-amd64%20%7C%20arm64-1f6feb">
  <img alt="Docker" src="https://img.shields.io/badge/Docker%20Hub-lord1egypt-2496ed?logo=docker&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## ✨ What runs

| Service | What it does | Image |
|---|---|---|
| **monerod** | Monero **v0.18.5.4** daemon on `--stagenet`, binaries GPG-verified at build time | `lord1egypt/monero-stagenet` |
| **exporter** | Exposes the daemon's metrics for Prometheus | `lord1egypt/monero-stagenet-exporter` |
| **nodemapper** | Turns the peer list into GeoIP metrics (world map of peers) | `lord1egypt/monero-stagenet-nodemapper` |
| **Prometheus** | Collects metrics from exporter and nodemapper | `prom/prometheus` |
| **Grafana** | **Node Stats** dashboard | `grafana/grafana` |
| **tor** | Relays your transactions over Tor, and serves the node as a hidden service | `lord1egypt/monero-stagenet-tor` |
| **i2pd** | Relays your transactions over i2p | `lord1egypt/monero-stagenet-i2p` |
| **explorer** | Web block explorer for your own node | `lord1egypt/monero-stagenet-explorer` |

Every image is **multi-arch (amd64 + arm64)**, so the same compose file runs on a PC, a Raspberry Pi, or an ARM phone running Linux.

## 🚀 Quick start

```bash
git clone https://github.com/Lord1Egypt/docker-monero-stagenet.git
cd docker-monero-stagenet
cp env-example .env          # optional: change ports, data dir, Grafana login
docker compose up -d         # pulls the prebuilt images
docker compose logs -f monerod
```

Then open:

| | URL |
|---|---|
| Grafana dashboard | http://localhost:3000 |
| Block explorer | http://localhost:8000 |
| Public (restricted) RPC for wallets | `http://<your-ip>:38089` |

The first sync downloads the whole stagenet chain (about 2.2 million blocks). Speed depends mostly on CPU. The **Tor onion address** of your node is printed at the start of `docker compose logs monerod`.

## 🔌 Ports (stagenet numbering)

| Port | Use | Exposed |
|---|---|---|
| `38080` | P2P | public |
| `38089` | Restricted RPC (safe for wallets: no mining or admin calls) | public |
| `38081` | Full RPC (exporter, nodemapper, explorer, solo mining) | `127.0.0.1` only |
| `38082` | ZMQ | `127.0.0.1` only |
| `38084` | Tor anonymous inbound | `127.0.0.1` only |

The full RPC can start mining and change the node's settings, so it is never published beyond this machine.

## ⛏️ Solo mining to your stagenet address

From the same machine:
```bash
curl -s http://127.0.0.1:38081/start_mining -d '{"miner_address":"5…your stagenet address…","threads_count":2,"do_background_mining":false,"ignore_battery":true}'
curl -s http://127.0.0.1:38081/mining_status
curl -s http://127.0.0.1:38081/stop_mining
```
Or point **XMRig** at it in solo mode: `xmrig --daemon -o 127.0.0.1:38081 -u 5…your address… --threads 2`.

## 🔧 Configuration (`.env`)

`DATA_DIR` (default `./data-stagenet`), `P2P_PORT`, `RESTRICTED_PORT`, `ZMQ_PORT`, `UNRESTRICTED_PORT`, `P2P_TOR`, `EXPLORER_PORT`, `GRAF_PORT`,
`PROM_RETENTION`, `GF_*` (Grafana login). Change `GF_SECURITY_ADMIN_PASSWORD` before publishing Grafana beyond localhost.

To reuse an already synced stagenet blockchain, point `DATA_DIR` at a **copy** of its folder: the one that contains `stagenet/lmdb`.

## 🏗️ Build and publish the images yourself

```bash
make build                       # build locally
./release.sh all [dockerhub-user]   # multi-arch build + push (needs docker login and buildx)
```

`docker-compose.full.yaml` compiles monerod from source instead of using the official release binaries.

## 🔄 What changed from upstream

This is a stagenet conversion of [lalanza808/docker-monero-node](https://github.com/lalanza808/docker-monero-node) (mainnet):

- `monerod --stagenet`, Monero **v0.18.5.4** with a fresh GPG-signed `hashes.txt` (binaryFate key `81AC 591F E9C4 B65C 5806 AFC3 F0AF 4D46 2A0B DF92`).
- All ports moved to the stagenet scheme above, in the daemon, the compose files, the Tor hidden services and the tools.
- **Fix:** nodemapper crashed (`KeyError: 'white_list'`) on a fresh node with no confirmed peers yet, so Prometheus showed it down.
- **Fix:** the exporter now always reaches the daemon on its container port. Before, changing `UNRESTRICTED_PORT` silently broke metrics.
- Images published as multi-arch `lord1egypt/monero-stagenet-*`; containers prefixed `stagenet_` so a mainnet stack can run next to it.

## 🙏 Credits and license

Original project and Grafana dashboard by **[lalanza808](https://github.com/lalanza808)**, MIT license (kept in `LICENSE`).
Explorer image: `lalanza808/moneroexplorer`, mirrored unchanged. Prometheus exporter: [cirocosta/monero-exporter](https://github.com/cirocosta/monero-exporter).
