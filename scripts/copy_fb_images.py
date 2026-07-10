import os, shutil
src_dir = r'C:\fb_images'
if not os.path.exists(src_dir):
    print('C:/fb_images not found')
    raise SystemExit(1)
user_dir = os.path.join('app','uploads','images','schedules','476720fe-579a-4ee6-8bc7-71a1b855533c')
os.makedirs(user_dir, exist_ok=True)
copied = []
for fname in os.listdir(src_dir):
    src = os.path.join(src_dir, fname)
    if os.path.isfile(src):
        dst = os.path.join(user_dir, fname)
        shutil.copy2(src, dst)
        copied.append(fname)
print('Copied', len(copied), 'files to', user_dir)
for f in copied[:100]:
    print(f)
