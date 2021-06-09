import os
import shutil
import re

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
    title = match.group(1)
    return '['+title+']('+path+title_to_fname(title)+')'
