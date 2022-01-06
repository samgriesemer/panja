import os
import shutil
import sys
import re
import logging
import hashlib

from tqdm import tqdm

def copy_file(ipath, opath):
    shutil.copy2(ipath, opath)
    
def directory_tree(path):
    '''Return list of paths for all non-hidden files _inside_ of `path`. '''
    paths = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        paths += [os.path.relpath(os.path.join(dirpath, file), path) \
                  for file in filenames if not \
                  any([dir.startswith('.') for dir in os.path.join(dirpath,file).split('/')])]
    return paths

def check_dir(path):
    '''Check if `path` exists, creating the necessary directories if not'''
    outdir = os.path.dirname(path)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

def fname_to_title(fname):
    return fname.replace('_', ' ')

def title_to_fname(title):
    title = re.sub(r' *\n *', ' ', title)
    return title.replace(' ', '_')

def title_to_link(match, path=''):
    '''Return Markdown-style link from file title'''
    title  = match.group(1)
    anchor = match.group(2)
    desc   = match.group(3)

    if desc: display = desc
    else:
        if anchor: display = title+anchor
        else: display = title

    return '['+display+']('+path+title_to_fname(title)+')'

def src_hash(module, src, ext=None):
    if ext is None: ext = ''
    shash = hashlib.sha1(src.encode(sys.getfilesystemencoding())).hexdigest()
    return module+shash+ext

class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
