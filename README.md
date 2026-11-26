# MIS2001 Week 11 - Exercise 2 (Data Workflow with Flask + SQLite + GitHub Actions)

## Structure
- `data/order.txt`, `data/customer.txt`: Raw input data (also supports additional `order*.txt` / `customer*.txt` files).
- `clean_and_merge.py`: Reads `data/`, removes duplicates, converts amounts to CNY (`USD=6.9`, `EUR=7.5`, `CNY=1.0`, `JPY=0.05`), merges on `customer_id`, and writes `merged_orders` and `region_summary` tables to `orders.db`.
- `app.py` + `templates/index.html`: Flask dashboard displaying both tables and automatically refreshing when `orders.db` changes.
- `.github/workflows/data_pipeline.yml`: Triggers whenever files in `data/` are pushed, runs `clean_and_merge.py`, and commits the updated `orders.db` back to the repository.

## Run Locally
```bash
pip install -r requirements.txt
python clean_and_merge.py
python app.py
```
Then open `http://127.0.0.1:5000`.
