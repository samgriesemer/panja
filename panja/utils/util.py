import os
import shutil
import subprocess
import sys
import re
import logging
import hashlib
from pathlib import Path
from colorama import Fore
import tqdm


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

    if desc:
        display = desc
    else:
        if anchor:
            display = title + anchor.replace('#','<span style="color:rgba(var(--violet-rgb),1.0)">§</span>')
        else:
            display = title

    article_name = title_to_fname(title)
    pdf = Path(article_name).suffix == '.pdf'
    if graph and graph.get_article(article_name):
        link_txt = '['+display+']('+str(Path('/',path,article_name+parse_anchor(anchor,
                graph.get_article(article_name).metadata.get('heading_map'))))+')'
    elif pdf:
        link_txt = '['+display+']('+str(Path('/pdf.html?file=',article_name))+')'
    else:
        link_txt = '['+display+']('+str(Path('/',path,article_name+parse_anchor(anchor)))+')'

    # button experiment
    simple = not (pdf or path)
    link_txt +=  '''<button 
                        class='arrow ssrc'
                        data-docsource="{}">←
                    </button>'''.format(str(Path('/',path,'simple' if simple else '',article_name)))

    return link_txt

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
    if hmap is not None and anchor_str[1:] in hmap:
        return '#'+hmap[anchor_str[1:]]

    m = re.findall(r'#[^#]*$', anchor_str)
    tail = m[-1] if m else ''
    tail = tail.lower().replace(' ', '-')
    tail = re.sub(r'[^\w\s-]','',tail)
    tail = '#'+tail if tail else tail
    return tail

def pdf_preview(pdf_path, img_path, only_mod=True):
    pdf_path = Path(pdf_path)
    img_path = Path(img_path)
    
    # only generate preview if needed
    if only_mod:
        if img_path.exists() and os.listdir(str(img_path)) != []:
            for file in os.listdir(str(img_path)):
                if Path(img_path,file).stat().st_mtime < pdf_path.stat().st_mtime:
                    break
                # all conditions met: non-empty, existing img path with all rendered
                # images at least as recent as the PDF file
                return False
        
        
    if img_path.exists(): shutil.rmtree(img_path)
    img_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pdftoppm',pdf_path,str(Path(img_path,'img')),'-png','-progress','-l','50'])


def src_hash(module, src, ext=None):
    if ext is None: ext = ''
    shash = hashlib.sha1(src.encode(sys.getfilesystemencoding())).hexdigest()
    return module+shash+ext

def color_str(str, fore_color):
    return fore_color + str + Fore.RESET

def bs(arr, t):
    if len(arr) == 0: return 0
    if len(arr) == 1:
        if t > arr[0]: return 1
        else: return 0

    mid = len(arr) // 2
    if arr[mid] == t:
        return mid
    elif t > arr[mid]:
        return mid+bs(arr[mid:],t)
    else:
        return bs(arr[:mid],t)

#class TqdmLoggingHandler(logging.Handler):
class TqdmLoggingHandler(logging.StreamHandler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            #tqdm.tqdm.write(msg)
            tqdm.tqdm.write(msg, end=self.terminator)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
