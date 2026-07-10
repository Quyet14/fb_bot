# Quick inspector: print recent post_schedules and fanpage_schedules docs
from pprint import pprint
import os, sys
# Ensure project root is on PYTHONPATH so `app` package imports work when running script directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app.mongo_db import get_collection

def print_docs(col_name, limit=5):
    try:
        col = get_collection(col_name)
        docs = list(col.find().sort('id', -1).limit(limit))
        print(f"--- {col_name} (latest {len(docs)}) ---")
        for d in docs:
            pprint({
                'id': d.get('id'),
                'user_id': d.get('user_id'),
                'thu': d.get('thu'),
                'gio': d.get('gio'),
                'dang_kem_anh': d.get('dang_kem_anh'),
                'image_mode': d.get('image_mode'),
                'image_paths': d.get('image_paths'),
            })
    except Exception as e:
        print(f"Error reading {col_name}: {e}")

if __name__ == '__main__':
    print_docs('post_schedules')
    print_docs('fanpage_schedules')
