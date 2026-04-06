# BURGERREICH_watch v3

Open-source US military force tracking dashboard.

All data sourced from **publicly available OSINT** and **official DoD releases**.

> **NOT AFFILIATED WITH DoD OR ANY GOVERNMENT ENTITY**

## Architecture

```
site/              Dashboard (single-file SPA)
  data/            JSON feeds consumed by the dashboard
collectors/        Python scripts that pull RSS + scrape COCOM sites
deploy/            Self-hosting configs (nginx, systemd, setup script)
.github/workflows/ GitHub Actions (collect every 6h + Pages deploy)
```

## Data Sources

| Collector | Source | Output |
|-----------|--------|--------|
| CENTCOM | centcom.mil | centcom.json |
| EUCOM | eucom.mil | eucom.json |
| INDOPACOM | pacom.mil | indopacom.json |
| AFRICOM | africom.mil | africom.json |
| STRATCOM | stratcom.mil | stratcom.json |
| OSINT | USNI, DoD News, CSIS, Janes | osint.json |
| Fleet | USNI Fleet Tracker | fleet.json |
| Casualties | CENTCOM / DoD releases | casualties.json |
| Losses | Multi-source news scrape | losses.json |
| Posture | CENTCOM / DoD releases | posture.json |
| Commanders | COCOM leadership pages | commanders.json |
| Doomsday | Bulletin of Atomic Scientists | doomsday.json |

## Self-Hosting on Raspberry Pi 4

### Option A: Bare metal (recommended for Pi4)

```bash
git clone https://github.com/mehidk69/Burgerreich-v3.git
cd Burgerreich-v3
sudo bash deploy/setup-pi.sh
```

This installs nginx, creates a Python venv, sets up a systemd timer (runs every 30min), and starts serving the dashboard. Done.

```
Dashboard:  http://<pi-ip>
Logs:       tail -f /var/log/burgerreich.log
Timer:      systemctl status burgerreich-collect.timer
Manual run: cd /opt/burgerreich && ./venv/bin/python run_all.py
```

### Option B: Docker

```bash
git clone https://github.com/mehidk69/Burgerreich-v3.git
cd Burgerreich-v3
docker compose up -d
```

Dashboard at `http://<pi-ip>:8080`. Data persists in Docker volumes.

### Option C: GitHub Pages (no self-hosting)

Collectors run every 6h via GitHub Actions and commit JSON to the repo. Enable GitHub Pages on the repo to serve the dashboard.

## Run Manually

```bash
# All collectors + merge in one command
python run_all.py

# Quick mode (skip slow scrapers)
python run_all.py --quick

# Individual collectors
cd collectors
pip install -r requirements.txt
python collect_centcom.py
python collect_fleet.py
python merge_feeds.py
```

## License

MIT
