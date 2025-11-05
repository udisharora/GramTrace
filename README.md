# Instagram Profile Scraper

A Flask-based web app to scrape public Instagram profile data.

## 📌 Features
- Input any Instagram username
- Scrapes and displays public data (followers, bio, etc.)
- Stores scrape history

## 🛠 Tech Stack
- Python 3
- Flask
- BeautifulSoup
- requests

## 🚀 Getting Started

### 🔧 Install Requirements

```bash
pip install -r requirements.txt
```

## How to run locally
```bash
python app.py
```
Then open the local domain and follow the steps on the website

# HDBSCAN Customer Clustering

This repository contains Python implementations and utilities for hierarchical density-based clustering (HDBSCAN) applied to customer data. It includes several module variants, data generation, and example output files (dendrograms & cluster assignments).

## Repository structure

- `HDBSCAN_module.py` - HDBSCAN implementation (original).
- `HDBSCAN_module2.py` - Alternate/optimized HDBSCAN implementation.
- `HDBSCAN_orig.py` - Another prior variant of HDBSCAN code.
- `main.py` - Example entrypoint that runs clustering on the provided dataset.
- `run.py` - Alternative script to run experiments and contains `PostgresHDBSCAN`.
- `generate_data.py` - Helper to generate synthetic customer data (`synthetic_customers.csv`).
- `synthetic_customers.csv` - Synthetic dataset used by examples.
- `customer_clusters.txt` - Example output with cluster assignments.
- `customer_dendrogram.txt` - Example dendrogram output.
- `optimized_dendrogram.txt` - Optimized dendrogram output.

## Requirements

- Python 3.8+ (tested on 3.11)

Required Python packages (based on the imports in the code):
- numpy
- pandas
- scikit-learn
- scipy
- hdbscan
- psycopg2-binary
- tqdm

Install Python dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy pandas scikit-learn scipy hdbscan psycopg2-binary tqdm
```

## PostgreSQL (local) installation and setup (macOS Homebrew)

Install and start PostgreSQL:
```bash
brew install postgresql
brew services start postgresql
```

Create database user and database (replace `yourpassword` with the desired password):
```bash
psql -U postgres -c "CREATE USER udisharora WITH PASSWORD 'yourpassword';"
psql -U postgres -c "CREATE DATABASE clustering_db OWNER udisharora;"
```

Test connection from terminal:
```bash
psql -h localhost -U udisharora -d clustering_db
```

Python quick test for DB connectivity:
```python
import psycopg2
conn = psycopg2.connect(host='localhost', dbname='clustering_db', user='udisharora', password='yourpassword', port=5432)
conn.close()
```

## Exact changes to `main.py` to connect to the local database

Replace the existing `PostgresHDBSCAN` instantiation with the following (fill `password` with the password you set above):

```python
hdb = PostgresHDBSCAN(
    host="localhost",
    dbname="clustering_db",
    user="udisharora",
    password="yourpassword",
    port=5432
)
```

`run.py` uses `psycopg2.connect(...)` under the hood, so no other changes are required in the code for connecting locally beyond providing the correct credentials in `main.py`.

## How to run

Generate synthetic data (optional):
```bash
python generate_data.py
```

Run the main clustering script:
```bash
python main.py
```

Or run the alternative script:
```bash
python run.py
```

Output files:
- `customer_clusters.txt` will be created when `save_results(..., to_txt=True)` is called.
- Database table `customer_clusters` will be created/overwritten if `save_results(..., to_db=True)` is used.

## Notes

- `main.py` calls `PostgresHDBSCAN.fetch_data("customer")`. If the `customer` table does not exist, `run.py`'s `PostgresHDBSCAN.create_sample_table` will create a sample `customer` table automatically.
- Use the exact pip install line above to ensure all required packages are installed before running the scripts.

