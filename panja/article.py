import re
import os
import inspect
import pypandoc as pp
from colorama import Fore
from collections import defaultdict

from .utils import util

class Article:
    '''
    Article object for operating on Markdown files. The class takes care of a lot of
    desired features automatically, stripping metadata out of YAML block, performing
    custom text transformations (like wiki links to Markdown style links), and
    converting the resulting text to HTML. This class is admittedly a bit sloppy and
    specific to my own needs at the moment.

    :param fullpath:

    :param name:

    :param verbose:

    :var link:

    '''
    def __init__(self, fullpath, name, verbose=True):
        self.fullpath = fullpath
        self.name = name

        self.link = name
        self.html = ''
        self.content = ''
        self.valid = True
        self.verbose = verbose

        # lightweight parsing
        self.metadata = self.process_metadata()

        if self.valid:
            self.links = self.process_links(self.content)

            # could build in backlink processing to a process_links-like function

    def process_metadata(self):
        with open(self.fullpath, 'r') as f:
            ft = f.read()
            mt = re.match('---\n(.*?)\n---', ft, flags=re.DOTALL)
            metadata = {}

            if mt is None:
                self.content = ft
                self.valid = False

                if self.verbose:
                    print(Fore.RED + '[invalid metadata] ' + Fore.RESET + self.name)

                return metadata

            self.content = ft.replace(mt.group(0), '')
            for line in mt.group(1).split('\n'):
                split = [line.split(':')[0], ':'.join(line.split(':')[1:])]
                attr, val = map(str.strip, split)
                metadata[attr.lower()] = val

            if 'tags' in metadata:
                metadata['tag_links'] = self.process_links(metadata['tags'])
            
            if 'series' in metadata:
                metadata['series_links'] = self.process_links(metadata['series'])

        return metadata

    def process_links(self, string):
        links = re.findall(
            pattern=r'\[\[([^\]`]*)\]\]',
            string=string
        )
        
        lcounts = defaultdict(int)
        for link in links:
            l = util.title_to_fname(link)
            lcounts[l] += 1

        return lcounts

    def transform_links(self, string, path=''):
        nt = re.sub(
            pattern=r'\[\[([^\]`]*)\]\]',
            repl=lambda x: util.title_to_link(x, path),
            string=string
        )

        return nt

    def transform_tasks(self, string):
        def repl(m):
            s = m.group(0)
            if m.group(1) == 'S':
                s = s.replace(m.group(1), ' ')
            if m.group(3) is not None:
                s = s.replace(m.group(3), '<span class="tight-box">'+m.group(3)+'</span>')    
            s = s.replace(m.group(4), '')

            if m.group(1) == 'S':
                s = s.replace(m.group(2), '<span style="color:green">'+m.group(2)+'</span>')
            return s

        nt = re.sub(
            pattern=r'\* \[(.)\] (.*?) ?(\([^\)]*\))?(  #\w{8})',
            repl=repl,
            string=string
        )

        return nt

    def convert_html(self, metamd=None, pdoc_args=None, filters=None):
        if metamd is None: metamd= []
        if pdoc_args is None: pdoc_args = []
        if filters is None: filters = []

        if self.metadata.get('toc') != 'false':
            pdoc_args.append('--toc')

        self.html = {}
        self.html.update(self.metadata)

        content = self.transform_links(self.content)
        content = self.transform_tasks(content)
        self.html['content'] = pp.convert_text(content,
                                               to='html5',
                                               format='md',
                                               extra_args=pdoc_args,
                                               filters=filters)

        # render extra metadata components to HTML
        for key in metamd:
            if key in self.metadata:
                if key == 'tags':
                    value = self.transform_links(self.metadata[key], 'tag/')
                else:
                    value = self.transform_links(self.metadata[key])

                html_text = pp.convert_text(value,
                                            to='html5',
                                            format='md',
                                            filters=filters)

                # strip out annoying <p> tags
                self.html[key] = re.sub(
                    pattern=r'^<p>(.*)</p>$',
                    repl=lambda m: m.group(1),
                    string=html_text
                )


