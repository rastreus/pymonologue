import sound
import os
import tempfile

path1 = '/tmp/smoke_test.m4a'
path2 = tempfile.gettempdir() + '/smoke_test.m4a'

print(f'/tmp exists: {os.path.exists("/tmp")}')
print(f'tempdir: {tempfile.gettempdir()}')
print(f'tempdir exists: {os.path.exists(tempfile.gettempdir())}')

for path in [path1, path2]:
    print(f'\n--- Testing {path} ---')
    try:
        r = sound.Recorder(path)
        print('Recorder created')
        r.record()
        print('Recording 3s...')
        import time; time.sleep(3)
        r.stop()
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f'File exists: {exists}, size: {size}')
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')
        
