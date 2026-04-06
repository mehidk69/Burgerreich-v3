# BURGERREICH_watch v3

Open-source US military force tracking dashboard.

All data sourced from **publicly available OSINT** and **official DoD releases**.

> **NOT AFFILIATED WITH DoD OR ANY GOVERNMENT ENTITY**

## Architecture

```
site/              GitHub Pages dashboard (single-file SPA)
  data/            JSON feeds consumed by the dashboard
collectors/        Python scripts that pull RSS + scrape COCOM sites
.github/workflows/ Automated collection (every 6h) + Pages deploy
```

## Data Sources

| Collector | Source | Feed |
|-----------|--------|------|
| CENTCOM | centcom.mil | RSS press releases |
| EUCOM | eucom.mil | RSS news |
| INDOPACOM | pacom.mil | RSS news |
| AFRICOM | africom.mil | RSS press releases |
| STRATCOM | stratcom.mil | RSS news |
| OSINT | USNI, ADS-B, CSIS | RSS/scrape |

## How It Works

1. **Collectors** run every 6 hours via GitHub Actions
2. Each collector pulls RSS feeds from combatant command websites
3. Items are classified by type (naval, air, ground, exercise, alert, posture)
4. `merge_feeds.py` consolidates all feeds into `site/data/feed.json`
5. Dashboard reads the merged feed and renders it

## Run Manually

```bash
cd collectors
pip install -r requirements.txt
python collect_centcom.py
python collect_eucom.py
python collect_indopacom.py
python collect_africom.py
python collect_stratcom.py
python collect_osint.py
python merge_feeds.py
```

## License

MIT
