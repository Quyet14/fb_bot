import requests, os, json
BASE='http://127.0.0.1:8000'
endpoints=['/schedules/dang-bai','/fanpage-schedules']
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for ep in endpoints:
    url = BASE + ep
    print('\n==', url)
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print('ERROR fetching', url, e)
        continue
    if not isinstance(data, list):
        print('Unexpected response:', type(data), data)
        continue
    for item in data:
        sid = item.get('id')
        mode = item.get('image_mode')
        paths = item.get('image_paths') or []
        dang_kem = item.get('dang_kem_anh')
        print(f'ID={sid} dang_kem_anh={dang_kem} image_mode={mode} image_paths={paths}')
        resolved=[]
        for p in paths:
            if not p:
                resolved.append((p, False))
                continue
            # resolve upload urls
            if p.startswith('/uploads/images/') or p.startswith('uploads/images/'):
                candidate = os.path.join(base_dir, p.lstrip('/'))
            elif os.path.isabs(p):
                candidate = p
            else:
                # search uploads
                found=None
                for root, dirs, files in os.walk(os.path.join(base_dir,'uploads','images')):
                    if os.path.basename(p) in files:
                        found=os.path.join(root, os.path.basename(p))
                        break
                candidate = found or p
            exists = os.path.exists(candidate) if candidate else False
            resolved.append((candidate, exists))
        print('  resolved:', json.dumps(resolved, ensure_ascii=False))

print('\nDone')
