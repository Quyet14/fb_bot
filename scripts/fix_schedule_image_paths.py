import sys, os, json
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
from app.mongo_db import get_collection

post_col = get_collection('post_schedules')
fan_col = get_collection('fanpage_schedules')

uploads_root = os.path.join(base_dir, 'app', 'uploads', 'images')
backup_file = os.path.join(base_dir, 'scripts', 'backup_schedule_image_paths.jsonl')

def find_file_by_name(name):
    for root, dirs, files in os.walk(uploads_root):
        if name in files:
            return os.path.join(root, name)
    return None

changed = []

for col, name in [(post_col,'post_schedules'), (fan_col,'fanpage_schedules')]:
    for doc in col.find({}):
        image_paths = doc.get('image_paths') or []
        if not image_paths:
            continue
        updated = False
        new_paths = []
        for p in image_paths:
            if not p:
                new_paths.append(p)
                continue
            if os.path.exists(p):
                new_paths.append(p)
                continue
            # try to find by basename
            b = os.path.basename(p)
            found = find_file_by_name(b)
            if found:
                new_paths.append(found)
                updated = True
            else:
                new_paths.append(p)
        if updated:
            # backup
            with open(backup_file,'a',encoding='utf8') as fh:
                fh.write(json.dumps({'col':name,'id':doc.get('id'),'before':doc}, ensure_ascii=False)+'\n')
            # update
            col.update_one({'_id':doc['_id']},{'$set':{'image_paths': new_paths}})
            changed.append({'col':name,'id':doc.get('id'),'new_paths':new_paths})

print('Done. Changes:', json.dumps(changed, ensure_ascii=False, indent=2))
print('Backup saved to', backup_file)
