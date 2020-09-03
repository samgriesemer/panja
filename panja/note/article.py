import re
import os
import inspect
import pypandoc as pp
from colorama import Fore

from ..utils import util

class Article:
    '''
    Article object for operating on Markdown files. The class takes care of a lot of
    desired features automatically, stripping metadata out of YAML block,
    performing custom text transformations (like wiki links to Markdown style
    links), and converting the resulting text to HTML. This class is admittedly
    a bit sloppy and specific to my own needs at the moment.
    '''
    def __init__(self, fullpath, name, basepath, local=False):
        self.fullpath = fullpath
        self.basepath = basepath
        self.name = name
        self.url = name
        self.metadata = {}
        self.html = ''
        self.valid = True
        self.metamd = ['summary']

        self.process_metadata()
        self.__dict__.update(self.metadata)

        # stop processing early if public and other
        if not local and (self.metadata.get('type') == 'journal' or
                          self.metadata.get('visibility') == 'private'):
            self.valid = False

    def process_metadata(self):
        with open(self.fullpath, 'r') as f:
            ft = f.read()
            mt = re.match('---\n(.*?)\n---', ft, flags=re.DOTALL)

            if mt is None:
                self.valid = False
                print(Fore.RED + '[invalid metadata] ' + Fore.RESET + self.name)
                return
            
            metadata = {}
            for line in mt.group(1).split('\n'):
                split = [line.split(':')[0], ':'.join(line.split(':')[1:])]
                attr, val = map(str.strip, split)
                metadata[attr.lower()] = val

            metadata['content'] = ft
        self.metadata = metadata

    def transform_links(self):
        nt = re.sub(
            pattern=r'\[\[([^\]`]*)\]\]',
            repl=util.title_to_link,
            string=self.metadata['content']
        )
        self.metadata['content'] = nt

    def convert_html(self):
        bpath = os.path.join('./', self.basepath)
        filters = [os.path.join(bpath, 'pandoc/filters/pandoc-katex/pandoc-katex.js')]
        pdoc_args = [
            '--section-divs',
            '--template={}'.format(os.path.join(self.basepath, 'pandoc/blank_template.html'))
        ]
       
        # conditional args
        if self.metadata.get('toc') != 'false':
            pdoc_args.append('--toc')

        self.transform_links()

        self.html = {}
        self.html.update(self.metadata)

        self.html['content'] = pp.convert_text(self.metadata['content'],
                                               to='html5',
                                               format='md',
                                               extra_args=pdoc_args,
                                               filters=filters)

        # render extra metadata components to HTML
        for key in self.metamd:
            if key in self.metadata:
                self.html[key] = pp.convert_text(self.metadata[key],
                                                 to='html5',
                                                 format='md',
                                                 filters=filters)


