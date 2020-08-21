import os
import shutil

def copy_file(self, ipath, opath):
    shutil.copy2(ipath, opath)
    
def directory_tree(self, path):
    '''Return list of paths for all non-hidden files __inside__ of `path`. '''
    paths = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        paths += [os.path.relpath(os.path.join(dirpath, file), path) \
                  for file in filenames if not file.startswith('.')]
    return paths

def check_dir(self, path):
    '''Check if `path` exists, creating the necessary directories if not'''
    outdir = os.path.dirname(path)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
