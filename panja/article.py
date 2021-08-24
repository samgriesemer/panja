import re
from collections import defaultdict
from datetime import datetime

import pypandoc as pp
import pandocfilters as pf
import misaka

from colorama import Fore

from . import utils

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
        self.html = {}
        self.raw_content = ''
        self.raw_lines = []
        self.content = ''
        self.valid = True
        self.verbose = verbose
        self.ctime = datetime.now().timestamp()

        # lightweight parsing
        self.metadata = self.process_metadata()
        self.links = {}
        self.tree = {}
        self.linkdata = {}

            # could build in backlink processing to a process_links-like function

    def process_metadata(self):
        with open(self.fullpath, 'r') as f:
            ft = f.read()
            self.raw_content = ft

            f.seek(0)
            self.raw_lines = f.readlines()

            metadata = {}
            mt = re.match('---\n(.*?)\n---', ft, flags=re.DOTALL)

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

    def context_tree(self):
        tree = {}
        current_header = {'c': ''}

        def comp(key, value, format, meta):
            if key == 'Header':
                #print(self.name)
                #print(value[2][0])
                #current_header['c'] = value[2][0]['c'][1][0]['c']

                title = []
                for v in value[2]:
                    for vc in v['c'][1:]:
                        outer = vc
                        #print('+++', outer[0])
                        if type(outer) == str:
                            title.append(outer)
                            continue
                        elif type(outer[0]) == str:
                            title.append(outer[0])
                            continue
                        elif 'c' in outer[0]:
                            title.append(outer[0]['c'])
                        else:
                            title.append(' ')
                current_header['c'] = ''.join([str(s) for s in title])

            if key == 'BulletList' or key == 'OrderedList':
                v = value if key == 'BulletList' else value[1]

                for item in v:
                    pos   = item[0]['c'][0][2][0][1].split('-')
                    start = pos[0][1:]
                    end   = pos[-1]

                    sl, sc = map(int, start.split(':'))
                    el, ec = map(int, end.split(':'))

                    obj = {
                        'c': [],
                        'p': tree.get(sl),
                        'v': ''.join(self.raw_lines[(sl-1):(el-1)]),
                        'h': current_header['c']
                    }

                    if obj['p'] is not None:
                        obj['p']['c'].append(obj)

                    for i in range(sl, el):
                        tree[i] = obj

            if key == 'Para':
                start = value[0]['c'][0][2][0][1].split('-')[0][1:]
                end   = value[-1]['c'][0][2][0][1].split('-')[-1]

                sl, sc = map(int, start.split(':'))
                el, ec = map(int, end.split(':'))

                obj = {
                    'c': [],
                    'p': None,
                    'v': ''.join(self.raw_lines[(sl-1):el]),
                    'h': current_header['c']
                }

                for i in range(sl, el+1):
                    if tree.get(i) is None:
                        tree[i] = obj

        cm = pp.convert_file(self.fullpath, format='commonmark+sourcepos', to='json')
        pf.applyJSONFilters([comp], cm)

        return tree

    def process_linkdata(self):
        links = re.finditer(
            pattern=r'\[\[([^\]`]*)\]\]',
            string=self.raw_content
        )

        linkdata = defaultdict(list)

        for m in links:
            # positional processing
            start = m.start()
            line = self.raw_content.count('\n', 0, start) +1
            col = start - self.raw_content.rfind('\n', 0, start)
            name = utils.title_to_fname(m.group(1))

            text = '(will be removed)'
            header = ''
            context = self.tree.get(line, '')
            if context:
                if context.get('p'):
                    header = context['p']['h']
                    text = context['p']['v']
                else:
                    header = context['h']
                    text = context['v']
           
            linkdata[name].append({
                'ref':  self,
                'line': line,
                'col':  col,
                'context': text,
                'header': str(header)
            })

        return linkdata

    def process_links(self, string):
        links = re.findall(
            pattern=r'\[\[([^\]`]*)\]\]',
            string=string
        )

        lcounts = defaultdict(int)
        for link in links:
            l = utils.title_to_fname(link)
            lcounts[l] += 1

        return lcounts

    def process_structure(self):
        self.links    = self.process_links(self.content)
        self.tree     = self.context_tree()
        self.linkdata = self.process_linkdata()

    def transform_links(self, string, path=''):
        nt = re.sub(
            pattern=r'\[\[([^\]`]*)\]\]',
            repl=lambda x: utils.title_to_link(x, path),
            string=string
        )

        return nt

    def transform_tasks(self, string):
        def repl(m):
            s = m.group(0)
            if m.group(1) == 'S':
                s = s.replace(m.group(1), ' ')
                s = s.replace(m.group(2), '<span style="color:green">'+m.group(2)+'</span>')
            if m.group(3):
                s = s.replace(m.group(3), '<span style="color:red">'+m.group(3)+'</span>')
            if m.group(4) is not None:
                s = s.replace(m.group(4), '<span class="tight-box">'+m.group(4)+'</span>')    
            s = s.replace(m.group(5), '')

            return s

        nt = re.sub(
            pattern=r'\* \[(.)\] (.*?) ?(!{1,3})? ?(\([^\)]*\))?(  #\w{8})',
            repl=repl,
            string=string
        )

        return nt

    def convert_html(self, metamd=None, pdoc_args=None, filters=None, fast=False):
        if metamd is None: metamd = []
        if pdoc_args is None: pdoc_args = []
        if filters is None: filters = []

        if self.metadata.get('toc') != 'false':
            pdoc_args.append('--toc')

        self.html = {}
        self.html.update(self.metadata)
        
        # these should really become pandoc filters, move function pandocfilters filters
        # in regular location; can be location for all future modifiers (like tikz!)
        content = self.transform_links(self.content)
        content = self.transform_tasks(content)

        if fast:
            self.html['content'] = misaka.html(content)
        else:
            # convert regular file content
            self.html['content'] = pp.convert_text(content,
                                                   to='html5',
                                                   format='md',
                                                   extra_args=pdoc_args,
                                                   filters=filters)

        # convert backlinks
        for linklist in self.linkdata.values():
            for link in linklist:
                context = self.transform_links(link['context'])
                if fast:
                    link['html'] = misaka.html(context)
                else:
                    link['html'] = pp.convert_text(context,
                                                   to='html5',
                                                   format='md',
                                                   filters=filters)

        # render extra metadata components to HTML
        for key in metamd:
            if key in self.metadata:
                if key == 'tags':
                    value = self.transform_links(self.metadata[key], 'tag/')
                else:
                    value = self.transform_links(self.metadata[key])

                if fast:
                    html_text = misaka.html(value)
                else:
                    html_text = pp.convert_text(value,
                                                to='html5',
                                                format='md',
                                                filters=filters)
                
                self.html[key] = re.sub(
                    pattern=r'^<p>(.*)</p>$',
                    repl=lambda m: m.group(1),
                    string=html_text
                )
