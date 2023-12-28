import pystray
from pystray import MenuItem as item
import pystray
from PIL import Image
import time
import threading
from typing import List
import os
import datetime
import shutil
import json
import traceback
import stat

THREADING = []
THREADING:List[threading.Thread]

CYCLE = 0.025 # n minute, each.
EVERY = 5 # if the folder size is not changing for 5 cycle, then execute the "folder moving"
MAX_SIZE = 300.0 # n GigaByte, each.

# ignore files in the inspect_path. those files will be gently ignored while replacing other files and folders.
IGNORED_FILE = ['desktop.ini',] 

# ignore folders in the inspect_path. those folders will be gently ignored while replacing other folders and folders.
# BUT, if folders are not directly belong to the inspect_path but placed inside of the subdirectories, this setting will not be applied.
IGNORED_FOLDER = ['.tmp.drivedownload', '.tmp.driveupload',] 

# inspect_path = './test' # this could be the cloud drive service's storage folder.
inspect_path = 'C:/Users/asdfg/내 드라이브(enzoescipy@gmail.com)' # this could be the cloud drive service's storage folder.
archive_path = './archive' # this is where your files are stored.

def make_dir_writable(function, path, exception):
    """The path on Windows cannot be gracefully removed due to being read-only,
    so we make the directory writable on a failure and retry the original function.
    """
    os.chmod(path, stat.S_IWRITE)
    function(path)

def kill(callback=None):
    global icon
    if callback != None:
        callback()
    print('process ends.')
    for thread in THREADING:
        pass
    icon.stop()

def mainloop():
    foldersize_history = []
    def get_size(start_path):
        total_size = 0
        for direct_path in os.listdir(start_path):
            full_path = os.path.join(start_path, direct_path)
            if direct_path in IGNORED_FILE + IGNORED_FOLDER:
                continue
            elif os.path.isdir(full_path):
                for dirpath, dirnames, filenames in os.walk(full_path):
                    for f in filenames:
                        if f in IGNORED_FILE:
                            continue
                        fp = os.path.join(dirpath, f)
                        # skip if it is symbolic link
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
            else:
                total_size += os.path.getsize(full_path)

        print(total_size)
        return total_size
    
    def copytree_ignore(source, destnation):
        os.mkdir(destnation)
        for direct_path in os.listdir(source):
            full_source_path = os.path.join(source, direct_path)
            full_dest_path = os.path.join(destnation, direct_path)
            if direct_path in IGNORED_FILE + IGNORED_FOLDER:
                continue
            elif os.path.isdir(full_source_path):
                shutil.copytree(full_source_path, full_dest_path)
            else:
                shutil.copyfile(full_source_path, full_dest_path)

    
    def archive(archive_path, inspect_path, size):
        total_archieved_byte = 0
        for path in os.listdir(archive_path):
            full_path = os.path.join(archive_path, path, '.archive_spec')
            with open(full_path, 'r') as f:
                spec_json = json.loads(''.join(f.readlines()))
                total_archieved_byte += spec_json['size']
        if total_archieved_byte / (1024**3) > MAX_SIZE:
            raise Exception("archive directory reached its maximum save limitation.")

        t = datetime.datetime.now()
        saved_path = f'{archive_path}/{t.year}_{t.month}_{t.day}_{t.hour}{t.minute}{t.second}'

        spec_dict = {}
        spec_dict['size'] = get_size(inspect_path)
        spec_dict['time'] = str(t)

        copytree_ignore(inspect_path, saved_path)
        with open(f'{saved_path}/.archive_spec', 'w') as f:
            f.write(json.dumps(spec_dict))
        if spec_dict['size'] != size:
            return False
        for path in os.listdir(inspect_path):
            if path in IGNORED_FILE + IGNORED_FOLDER:
                continue
            full_path = f'{inspect_path}/{path}'
            if os.path.isdir(full_path):
                shutil.rmtree(full_path, onerror=make_dir_writable)
            else:
                os.remove(full_path)
        
    while True:
        try:
            print("i am iter")
            foldersize_history.append(get_size(inspect_path))
            if len(foldersize_history) > EVERY:
                foldersize_history.pop(0)
                if foldersize_history[0] != 0 and foldersize_history.count(foldersize_history[0]) >= EVERY:
                    archive(archive_path, inspect_path, foldersize_history[0])
                    print("archive succeed.")
                    foldersize_history.clear()
            print(foldersize_history)
            time.sleep(60*CYCLE)
        except Exception:
            try:
                t = datetime.datetime.now()
                saved_path = f'{t.year}_{t.month}_{t.day}_{t.hour}{t.minute}{t.second}'
                with open(f'./crashLog_{saved_path}.txt', 'w') as f:
                    f.write(traceback.format_exc())
                return
            except Exception:
                print(traceback.format_exc())
                return
            


iter_thread = threading.Thread(target=kill, args=(mainloop,), daemon=True)
iter_thread.start()
THREADING.append(iter_thread)

image = Image.open("icon.jpg")
menu = (item('exit', kill), item('exit', kill))
icon = pystray.Icon("name", image, "title", menu)
icon.run()