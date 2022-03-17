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

def title_to_link(match, path='', graph=None):
    '''Return Markdown-style link from file title'''
    title  = match.group(1) if match.group(1) else '' 
    anchor = match.group(2) if match.group(2) else ''
    desc   = match.group(3) if match.group(3) else ''

    if desc: display = desc
    else:
        if anchor:
            display = title + anchor.replace('#','<span style="color:rgba(var(--violet-rgb),1.0)">§</span>')
        else: display = title

    article_name = title_to_fname(title)
    if graph and graph.get_article(article_name):
        return '['+display+']('+path+article_name+parse_anchor(anchor,
                graph.get_article(article_name).metadata.get('heading_map'))+')'
    else:
        return '['+display+']('+path+article_name+parse_anchor(anchor)+')'

def parse_anchor(anchor_str, hmap=None):
    '''
    Problem here is we need context to fully recover the possible IDs added to the end of
    the section. Can get a close approximation by replacing spaces with dashes, but the
    full solution is much more complicated. I would need to be able to turn full
    subsection trajectories into a single anchor level with ID from outside of the page.
    So this could happen when processing each article's structure and mapping the full
    nested subsection names that we'd be expecting to use as anchors to the flat anchor
    name that Pandoc uses in the TOC. But this solution should suffice for now.
    '''
    if hmap is not None:
        return '#'+hmap[anchor_str[1:]]

    m = re.findall(r'#[^#]*$', anchor_str)
    tail = m[-1] if m else ''
    tail = tail.lower().replace(' ', '-')
    tail = re.sub(r'[^\w\s-]','',tail)
    return tail


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
