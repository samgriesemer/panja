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
    def __init__(self, fullpath, name, basepath, local=False, verbose=False):
        self.fullpath = fullpath
        self.basepath = basepath
        self.name = name
        self.link = name
        self.metadata = {}
        self.html = ''
        self.content = ''
        self.valid = True
        self.verbose = verbose
        self.metamd = ['summary', 'source', 'tags']

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
            self.content = ft

            if mt is None:
                self.valid = False
                if self.verbose:
                    print(Fore.RED + '[invalid metadata] ' + Fore.RESET + self.name)
                return
            
            metadata = {}
            for line in mt.group(1).split('\n'):
                split = [line.split(':')[0], ':'.join(line.split(':')[1:])]
                attr, val = map(str.strip, split)

                if attr == 'tags' and val != '':
                    metadata['tag_list'] = [util.title_to_fname(s[2:-2]) for s in re.split(', (?=\[)', val)]

                metadata[attr.lower()] = val

        self.metadata = metadata

    def transform_links(self, string, tag=False):
        nt = re.sub(
            pattern=r'\[\[([^\]`]*)\]\]',
            repl=lambda x: util.title_to_link(x, tag),
            string=string
        )

        return nt

    def transform_tasks(self, string):
        nt = re.sub(
            pattern=r'\* \[.\] .* (#\w{8})',
            repl=lambda m: m.group(0).replace(m.group(1), ''),
            string=string
        )

        return nt

    def convert_html(self):
        bpath = os.path.join('./', self.basepath)
        filters = [
            os.path.join(bpath, 'pandoc/filters/pandoc-katex/pandoc-katex.js'),
            os.path.join(bpath, 'pandoc/filters/pandoc-mermaid/index.js'),
        ]

        template_file = 'pandoc/no_toc_template.html' 
        if self.metadata.get('toc') != 'false':
            template_file = 'pandoc/blank_template.html'

        pdoc_args = [
            '--section-divs',
            '--template={}'.format(os.path.join(self.basepath, template_file))
        ]
       
        # conditional args
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
        for key in self.metamd:
            if key in self.metadata:
                if key == 'tags':
                    value = self.transform_links(self.metadata[key], True)
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


