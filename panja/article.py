import re
from collections import defaultdict
from datetime import datetime
import subprocess as subp
from pathlib import Path

import pandocfilters as pf
import misaka

from colorama import Fore

from . import utils

# captures base link, anchors, display text; any combo of them
link_regex = re.compile('\[\[([^\]]*?)(#[^\]]*?)?(?:\|([^\]]*?))?\]\]')
reflink_regex = re.compile('\[(\w*)\]: (http[^\s]*) ?(?:\(([^\)]*)\))?')
heading_regex = re.compile('(#{1,6}) (.*)')

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
        self.headings = []

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
            mt = re.match('---\n(.*?)\n(---|\.\.\.)', ft, flags=re.DOTALL)

            if mt is None:
                self.content = ft
                self.valid = False

                if self.verbose:
                    print(Fore.RED + '[invalid metadata] ' + Fore.RESET + self.name)

                return metadata

            self.content = ft.replace(mt.group(0), '')
            #for line in mt.group(1).split('\n'):
                #split = [line.split(':')[0], ':'.join(line.split(':')[1:])]
                #attr, val = map(str.strip, split)
                #metadata[attr.lower()] = val

            # doesnt face issues if metadata components have colon and are only
            # one line, but when multiline colons can have unexpected effects
            for m in re.findall('.*:[^:]*$', mt.group(1), flags=re.MULTILINE):
                split = [m.split(':')[0], ':'.join(m.split(':')[1:])]
                attr, val = map(str.strip, split)
                metadata[attr.lower()] = val

            if 'tags' in metadata:
                metadata['tag_links'] = self.process_links(metadata['tags'])
            
            if 'series' in metadata:
                metadata['series_links'] = self.process_links(metadata['series'])

            if 'files' in metadata:
                metadata['files_links'] = self.process_links(metadata['files'])

            public_carousel_html, local_carousel_html, public_files, local_files = self.get_carousels(metadata)
            metadata['public_carousel_html'] = public_carousel_html
            metadata['local_carousel_html']  = local_carousel_html
            metadata['public_files']         = public_files
            metadata['local_files']          = local_files

            # parse ref links
            metadata['reflinks'], metadata['sources'] = self.process_reflinks(self.content)

            # parse heading IDs
            metadata['heading_map'] = self.process_headings(self.content)
            print(metadata['heading_map'])

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
                    pos   = item[0]['c'][0][2][0][1].split('@')[-1].split('-')
                    start = pos[0]
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
                start = value[0]['c'][0][2][0][1].split('@')[-1].split('-')[0]
                end   = value[-1]['c'][0][2][0][1].split('@')[-1].split('-')[-1]

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

        #cm = pp.convert_file(self.fullpath, format='commonmark+sourcepos', to='json')
        cm = subp.check_output(["pandoc", "--from", "commonmark+sourcepos", "--to", "json", self.fullpath])
        pf.applyJSONFilters([comp], cm)

        return tree

    def process_linkdata(self):
        links = link_regex.finditer(self.raw_content)
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
            else: continue
           
            linkdata[name].append({
                'ref':  self,
                'line': line,
                'col':  col,
                'context': text,
                'header': str(header)
            })

        return linkdata

    def process_links(self, string):
        links = link_regex.findall(string)
        lcounts = defaultdict(int)

        for link in links:
            l = utils.title_to_fname(link[0])
            lcounts[l] += 1

        return lcounts

    def process_structure(self):
        self.links    = self.process_links(self.content)
        self.tree     = self.context_tree()
        self.linkdata = self.process_linkdata()
        print(self.headings)

    def process_reflinks(self, string):
        links = reflink_regex.findall(string)
        link_iter = reflink_regex.finditer(string)

        raw_reflink = '\n'.join(map(lambda x: x.group(0), link_iter))

        ref_group = []
        for link in links:
            ref_group.append('- [{}][{}]'.format(
                link[2] if link[2] else re.sub(r'^https?:\/\/','',link[1]),
                link[0],
            ))
        ref_group = '\n'.join(ref_group)+'\n\n'+raw_reflink

        return raw_reflink, ref_group

    def process_headings(self, string):
        headings = heading_regex.finditer(string)
        hmap = {}
        hset = set()
        level_stack = [0]
        hstack = []

        for heading in headings:
            print('heading: {}'.format(heading))
            hsize = len(heading.group(1))

            while level_stack[-1] >= hsize:
                hstack.pop()
                level_stack.pop()

            hstack.append(heading.group(2))
            level_stack.append(hsize)

            anchor_str = '#'.join(hstack)
            parse_target = hstack[-1]
            parse_target = parse_target.lower().replace(' ', '-')
            parse_target = re.sub(r'[^\w\s-]','',parse_target)
            cand_target = parse_target
            nid = 0

            while cand_target in hset:
                nid += 1
                cand_target = parse_target+'-{}'.format(nid)

            hmap[anchor_str] = cand_target
            hset.add(cand_target)

        return hmap
        

    def transform_links(self, string, path='', graph=None):
        nt = re.sub(
            pattern=link_regex,
            repl=lambda x: utils.title_to_link(x, path, graph),
            string=string
        )
        return nt

    def transform_tasks(self, string):
        def repl(m):
            # probably not the best practice using blanket replace statements
            s = m.group(0)
            if m.group(1) == '[S]':
                s = s.replace(m.group(1), '[ ]')
                s = s.replace(m.group(2), '<span style="background:var(--hl-green)">'+m.group(2)+'</span>')
            if m.group(3):
                s = s.replace(m.group(3), '<span style="color:var(--red)">'+m.group(3)+'</span>')
            if m.group(4) is not None:
                s = s.replace(m.group(4), '<span class="tight-box">'+m.group(4)+'</span>')    
            if m.group(5) is not None:
                s = s.replace(
                        m.group(5),
                        '<sup><a href="/task-{}">+</a></sup>'.format(m.group(6).replace('  #',''))
                    )
            s = s.replace(m.group(6), '')
            return s

        nt = re.sub(
            pattern=r'\* (\[.\]) (.*?) ?(!{1,3})? ?(\(\d[^\)]*\))? ?(\+\+)?(  #\w{8})',
            repl=repl,
            string=string
        )

        return nt

    def transform_task_headers(self, string):
        def repl(m):
            title = m.group(1)
            body  = m.group(3)
            s = '<details class="tasks"><summary>{}<hr class="solid"></summary>\n{}\n</details>'.format(title, body)
            return s

        nt = re.sub(
            pattern=r'#{1,6} (.*?) \| (.+)\n((?:.+(?:\n|$))*)',
            repl=repl,
            string=string
        )

        return nt
    
    def transform_tikz(self, string):
        '''
        Transforms raw TikZ to SVG and embeds the link in the Markdown source. If TikZ is
        standalone, will wrap the resulting SVG in image syntax. If TikZ source is
        detected in image syntax (enabling convenient captioning), the source will simply
        be replaced with the filename.
        '''
        def repl(m):
            caption  = m.group(1)
            tikz_src = m.group(2)

            svg_full_prefix = '/home/smgr/Documents/notes/images/'
            svg_site_prefix = 'images/'

            # generate stem filename from source hash
            svg_stem = utils.src_hash('livetex_', tikz_src, '.svg')
            svg_full_path = str(Path(svg_full_prefix, svg_stem))
            svg_site_path = str(Path(svg_site_prefix, svg_stem))

            # convert tikz to svg
            # note: can safely ignore re-render since name is based on source hash
            if not Path(svg_full_path).exists():
                print(Fore.YELLOW + 'Rendering TikZ SVG {}'.format(svg_stem))
                utils.tex.tikz2svg(tikz_src, svg_full_path)

            return '![{}]({})'.format(caption, svg_site_path)

        nt = re.sub(
            pattern=r'!\[(.*?)\]\(\n?(\\begin{tikzpicture}.*?\\end{tikzpicture})\n?\)',
            repl=repl,
            string=string,
            flags=re.DOTALL
        )

        return nt

    def transform_pdftex(self, string):
        '''
        Transforms .pdf_tex files that are linked within Markdown images
        '''
        def repl(m):
            caption  = m.group(1)
            texpdf = m.group(2)

            in_full_prefix = '/home/smgr/Documents/notes/'
            svg_full_prefix = '/home/smgr/Documents/notes/images/'
            svg_site_prefix = 'images/'

            # generate stem filename from source hash
            in_full_path = str(Path(in_full_prefix, texpdf))
            tex_src = ''
            with open(in_full_path+'.pdf_tex', 'r') as f:
                tex_src = f.read()

            svg_stem = utils.src_hash('pdftex_', tex_src, '.svg')
            svg_full_path = str(Path(svg_full_prefix, svg_stem))
            svg_site_path = str(Path(svg_site_prefix, svg_stem))

            # convert tikz to svg
            # note: can safely ignore re-render since name is based on source hash
            if not Path(svg_full_path).exists():
                print(Fore.YELLOW + 'Rendering PDF TeX {} as {}'.format(texpdf, svg_stem))
                utils.tex.pdftex2svg(
                    in_full_path+'.pdf_tex',
                    in_full_path+'.pdf',
                    svg_full_path)

            return '![{}]({})'.format(caption, svg_site_path)

        nt = re.sub(
            pattern=r'!\[(.*?)\]\((.*?)\.pdf_tex\)',
            repl=repl,
            string=string,
            flags=re.DOTALL
        )

        return nt

    def get_carousels(self, metadata):
        public_carousel_str = ''
        local_carousel_str = ''
        public_files = {}
        local_files = {}

        for link in metadata.get('files_links', []):
            try:
                stem = Path(link).relative_to('docs')
            except ValueError:
                print('File attribute link "{}" not properly located'.format(link))
                continue
             
            reg_src = Path('/home/smgr/Documents/notes/images/pdf/', stem)
            ann_src = Path('/home/smgr/Documents/notes/images/pdf/rm/docs/', stem)

            if reg_src.exists():
                public_carousel_str += self.carousel_html(str(stem), str(reg_src))
                public_files[str(stem)] = str(Path('/docs/', stem))
            if ann_src.exists():
                name = 'rm/docs/'+str(stem)
                local_carousel_str += self.carousel_html(name, str(ann_src))
                local_files[name] = str(Path('/docs/', name))

        note_src = Path('/home/smgr/Documents/notes/images/pdf/rm/', self.name).with_suffix('.pdf')
        if note_src.exists():
            name = 'rm/'+self.name+'.pdf'
            local_carousel_str += self.carousel_html(name, str(note_src))
            local_files[name] = str(Path('/docs/', self.name))

        return public_carousel_str, local_carousel_str, public_files, local_files

    def carousel_html(self, name, path):
        outstr = '<div class="inner-carousel-wrapper" style="display:none;">'
        outstr += '<div style="font-weight:bold;border-bottom:1px solid;color:black;">{}</div>'.format(name)
        outstr += '<div class="carousel" data-docsource="{}">'.format(name)
        for img in sorted(utils.directory_tree(path)):
            outstr += '<div class="card"><img src="/images/pdf/'+name+'/'+img+'"></div>'
        outstr += '</div></div>'
        return outstr

    def conversion_wrapper(self, content, extra_args=None, filters=None):
        if extra_args is None: extra_args = []
        if filters is None: filters = []

        cmd = ['pandoc', '--from', 'markdown', '--to', 'html5']
        cmd += extra_args
        cmd += [e for f in filters for e in ['-F', f]]

        c = subp.check_output(cmd, text=True, input=content, stderr=subp.DEVNULL)
        return c


    def convert_html(self, metamd=None, pdoc_args=None, filters=None, fast=False, graph=None):
        if metamd is None: metamd = []
        if pdoc_args is None: pdoc_args = []
        if filters is None: filters = []

        if self.metadata.get('toc') != 'false':
            pdoc_args.append('--toc')

        self.html = {}
        self.html.update(self.metadata)
        
        # these should really become pandoc filters, move function pandocfilters filters
        # in regular location; can be location for all future modifiers (like tikz!)
        content = self.transform_links(self.content, graph=graph)
        content = self.transform_task_headers(content)
        content = self.transform_tasks(content)
        content = self.transform_tikz(content)
        content = self.transform_pdftex(content)

        try:
            if fast:
                self.html['content'] = misaka.html(content)
            else:
                # convert regular file content
                self.html['content'] = self.conversion_wrapper(content,
                                                       extra_args=pdoc_args,
                                                       filters=filters)
        except RuntimeError:
            print(Fore.RED + 'Pandoc failed to convert content in file '+ self.name)
            raise

        # convert backlinks
        for linklist in self.linkdata.values():
            for link in linklist:
                context = self.transform_links(link['context'])
                if fast:
                    link['html'] = misaka.html(context)
                else:
                    link['html'] = self.conversion_wrapper(context, 
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
                    html_text = self.conversion_wrapper(value, 
                                                        filters=filters)
                
                self.html[key] = re.sub(
                    pattern=r'^<p>(.*)</p>$',
                    repl=lambda m: m.group(1),
                    string=html_text
                )
