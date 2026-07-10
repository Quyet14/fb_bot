import sys, os, json
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
from app.mongo_crud_adapter import store

print('Listing post_schedules (Mongo adapter)')
for sch in store.list_post_schedules(None):
    print('\nID', sch.id, 'dang_kem_anh=', getattr(sch,'dang_kem_anh',False), 'image_mode=', getattr(sch,'image_mode',None))
    paths = getattr(sch,'image_paths',[]) or []
    resolved=[]
    for p in paths:
        if not p:
            resolved.append((p,False))
            continue
        if os.path.isabs(p):
            candidate=p
        elif p.startswith('/uploads/images/') or p.startswith('uploads/images/'):
            candidate=os.path.join(base_dir, p.lstrip('/'))
        else:
            # search
            found=None
            for root,dirs,files in os.walk(os.path.join(base_dir,'uploads','images')):
                if os.path.basename(p) in files:
                    found=os.path.join(root, os.path.basename(p))
                    break
            candidate=found or p
        exists=os.path.exists(candidate) if candidate else False
        resolved.append((candidate,exists))
    print(' image_paths:', json.dumps(paths, ensure_ascii=False))
    print(' resolved:', json.dumps(resolved, ensure_ascii=False))

print('\nListing fanpage_schedules (Mongo adapter)')
for sch in store.list_fanpage_schedules(None):
    print('\nID', sch.id, 'dang_kem_anh=', getattr(sch,'dang_kem_anh',False), 'image_mode=', getattr(sch,'image_mode',None))
    paths = getattr(sch,'image_paths',[]) or []
    resolved=[]
    for p in paths:
        if not p:
            resolved.append((p,False))
            continue
        if os.path.isabs(p):
            candidate=p
        elif p.startswith('/uploads/images/') or p.startswith('uploads/images/'):
            candidate=os.path.join(base_dir, p.lstrip('/'))
        else:
            # search
            found=None
            for root,dirs,files in os.walk(os.path.join(base_dir,'uploads','images')):
                if os.path.basename(p) in files:
                    found=os.path.join(root, os.path.basename(p))
                    break
            candidate=found or p
        exists=os.path.exists(candidate) if candidate else False
        resolved.append((candidate,exists))
    print(' image_paths:', json.dumps(paths, ensure_ascii=False))
    print(' resolved:', json.dumps(resolved, ensure_ascii=False))

print('\nDone')
