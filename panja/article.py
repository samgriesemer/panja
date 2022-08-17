import re
from collections import defaultdict
from datetime import datetime
import subprocess as subp
from pathlib import Path
import yaml

import pandocfilters as pf
import misaka

from colorama import Fore

from . import task
from . import utils

# captures base link, anchors, display text; any combo of them
link_regex = re.compile('\[\[([^\]]*?)(#[^\]]*?)?(?:\|([^\]]*?))?\]\]')
reflink_regex = re.compile('\[(\w*)\]: (http[^\s]*) ?(?:\(([^\)]*)\))?(?:"([^"]*)")?')
bookmark_regex = re.compile('\[([a-zA-Z]{1,2})\]: (http[^\s]*) ?(?:\(([^\)]*)\))?(?:"([^"]*)")?')
heading_regex = re.compile('(#{1,6}) (.*)')
data_regex = re.compile('# Data\s+```yaml\s([\s\S]*?)\s+```')

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
        self.raw_metadata = ''
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
            f.seek(0)
            self.raw_content = ft
            self.raw_lines   = f.readlines()

            metadata = {'name':self.name}
            mt = re.match('---\n(.*?)\n(---|\.\.\.)', ft, flags=re.DOTALL)

            if mt is None:
                self.content = ft
                self.valid = False

                if self.verbose:
                    print(Fore.RED + '[invalid metadata] ' + Fore.RESET + self.name)

                return metadata

            self.raw_metadata = mt.group(0)
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
            metadata['reflinks'], metadata['sources'], metadata['reflink_list'] = self.process_reflinks(self.content)
            metadata['bookmarks'], _, metadata['bookmark_list'] = self.process_bookmarks(self.content)

            # parse heading IDs
            metadata['heading_map'] = self.process_headings(self.content)

            # process data
            metadata['filedata'] = self.process_data(self.content)

            # process data
            metadata['citedata'] = self.process_bibdata(
                metadata.get('source'),
                metadata.get('citekey'),
                metadata.get('url'),
            )
            metadata['bibtex'] = metadata['citedata'].get('bibtex','')
            metadata['bibtex_quote'] = '```\n{}\n```'.format(metadata['bibtex'])

            if metadata.get('citekey'):
                metadata['citegen'] = '<b>[inline]</b> @{}'.format(metadata['citekey'])
            elif metadata['citedata'].get('citekey'):
                metadata['citegen'] = '<b>[inline]</b> @{}'.format(metadata['citedata']['citekey'])

            # task groups (for gantt primarily)
            metadata['task_groups'], metadata['task_list'] = self.process_task_groups(self.content)

            if metadata['task_groups']:
                metadata['task_gantt'] = task.taskdict_to_gantt_raw({
                    section: task.get_tasks_from_ids(tasks)
                    for section, tasks in metadata['task_groups'].items()
                }, 'Task Gantt')

                metadata['task_comp'] = ''.join([
                    self.transform_task_headers(self.transform_tasks(m), op=True)
                    for m in metadata['task_list']
                ])

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
                    if not item:
                        print(Fore.YELLOW + '\n[empty list item]' + Fore.RESET)
                        continue

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

    def process_linkdata(self, string, offset=0):
        '''
        Offset parameter to allow correction for strings that do not match
        the content the self.tree is based on. Line numbers need to be shifted
        in order for matches to align on proper lines. Mainly for metadata restriction
        currently
        '''
        links = link_regex.finditer(string)
        linkdata = defaultdict(list)

        for m in links:
            # positional processing
            start = m.start()
            line = string.count('\n', 0, start) +1
            col = start - string.rfind('\n', 0, start)
            name = utils.title_to_fname(m.group(1))

            text = '(will be removed)'
            header = ''
            context = self.tree.get(line+offset, '')
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
        self.linkdata = self.process_linkdata(self.content, self.raw_metadata.count('\n'))

    def process_reflinks(self, string):
        links = reflink_regex.findall(string)
        link_iter = reflink_regex.finditer(string)

        raw_reflink = '\n'.join(map(lambda x: x.group(0), link_iter))

        ref_group = []
        triplets = []
        for link in links:
            name = link[2] if link[2] else re.sub(r'^https?:\/\/','',link[1])
            ref_group.append('- [{}][{}]'.format(
                name,
                link[0],
            ))
            triplets.append((link[0], link[1], name))

        ref_group = '\n'.join(ref_group)+'\n\n'+raw_reflink
        return raw_reflink, ref_group.strip(), triplets

    def process_bookmarks(self, string):
        # not currently excluded from the reflink parser
        links = bookmark_regex.findall(string)
        link_iter = bookmark_regex.finditer(string)

        raw_bookmark = '\n'.join(map(lambda x: x.group(0), link_iter))

        ref_group = []
        triplets = []
        for link in links:
            name = link[2] if link[2] else re.sub(r'^https?:\/\/','',link[1])
            ref_group.append('- [{}][{}]'.format(
                name,
                link[0],
            ))
            triplets.append((link[0], link[1], name))

        ref_group = '\n'.join(ref_group)+'\n\n'+raw_bookmark
        return raw_bookmark, ref_group.strip(), triplets


    def process_headings(self, string):
        headings = heading_regex.finditer(string)
        hmap = {}
        hset = set()
        level_stack = [0]
        hstack = []

        for heading in headings:
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

    def process_data(self, string):
        yamld = data_regex.findall(string)
        if yamld:
            try:
                parsed_yaml = yaml.safe_load(yamld[0])
            except yaml.YAMLError as e:
                print('YAML parse error in {}'.format(self.name))
                return None
            return parsed_yaml
        return None

    def process_task_groups(self, string):
        section_regex = re.compile(r'#{1,6} (.*?) \| (.+)\n((?:.+(?:\n|$))*)')
        task_regex = re.compile(r'\* (\[.\]) (.*?) ?(!{1,3})? ?(\(\d[^\)]*\))? ?(\+\+)?  #(\w{8})')
        
        section_dict = {}
        section_list = []
        for section in section_regex.finditer(string):
            section_head = section.group(1)
            section_body = section.group(3)
            task_list = [task.group(6) for task in task_regex.finditer(section_body)]
            section_dict[section_head] = task_list
            section_list.append(section.group(0))

        return section_dict, section_list

    def process_bibdata(self, source=None, citekey=None, url=None):
        '''
        Should ultimately make calls to a (prebuilt?) DocSync object so we aren't
        re-indexing the bib every article. Could consider just making this completely
        external, handled the way the graph association is.
        '''
        BIBTEX_ENTRY_REGEX = re.compile('^@.*{(.*),\n[\s\S]*?\n}',re.MULTILINE)
        BIBTEX_SOURCE_REGEX  = re.compile('^[^\S\r\n]*?file[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)
        BIBTEX_URL_REGEX  = re.compile('^[^\S\r\n]*?archive_url[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)
        BIBTEX_INF_URL_REGEX  = re.compile('^[^\S\r\n]*?url[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)

        bib_path  = Path('/home/smgr/Documents/notes/docs/docsyncbib.bib')
        wiki_path = Path('/home/smgr/Documents/notes/')

        source  = source.strip() if source is not None else ''
        citekey = citekey.strip() if citekey is not None else ''
        url     = url.strip() if url is not None else ''

        bib_ent_by_source  = {}
        bib_ent_by_citekey = {}
        bib_ent_by_url     = {}
        bib_ent_by_inf_url = {}

        bib_content = bib_path.open().read()
        for m in BIBTEX_ENTRY_REGEX.finditer(bib_content):
            bib_entry   = m.group(0)
            bib_citekey = m.group(1)
            bib_source  = BIBTEX_SOURCE_REGEX.search(bib_entry)
            bib_url     = BIBTEX_URL_REGEX.search(bib_entry)
            bib_inf_url = BIBTEX_INF_URL_REGEX.search(bib_entry)

            if bib_source:
                bib_source = bib_source.group(1)
                bib_source = str(Path(bib_source).relative_to(wiki_path))
            else:
                bib_source = ''

            if bib_url:
                bib_url = bib_url.group(1).strip()
            else:
                bib_url = ''

            if bib_inf_url:
                bib_inf_url = bib_inf_url.group(1).strip()
            else:
                bib_inf_url = ''

            bib_data = {
                'source':  bib_source,
                'citekey': bib_citekey,
                'url':     bib_url,
                'inf_url': bib_inf_url,
                'bibtex':  bib_entry,
            }

            bib_ent_by_citekey[bib_citekey] = bib_data
            if bib_source:
                bib_ent_by_source[bib_source] = bib_data
            if bib_url:
                bib_ent_by_url[bib_url] = bib_data
            if bib_inf_url:
                bib_ent_by_inf_url[bib_inf_url] = bib_data

        # feed pages mostly defined around a URL
        res = None
        if citekey:
            res = bib_ent_by_citekey.get(citekey)

        if url and not res:
            res = bib_ent_by_url.get(url)

        if url and not res:
            res = bib_ent_by_inf_url.get(url)
            if res is not None:
                # archive_url did not match url in the file; set canonical
                # URL to the inferred one, since this is what matches the url in
                # the file.
                res['url'] = res['inf_url']

        if source and not res:
            m = re.match(r'(?:\[\[)?([^\]\[]*)(?:\]\])?', source)
            if m: 
                rel_src = m.group(1)
                ful_src = Path(rel_src)
                res = bib_ent_by_source.get(str(ful_src))

            if res is not None:
                # url in document did not match either archive_url or the
                # inferred url. One or both may be defined, however, for the
                # source file. Default to keeping the archive_url since this is
                # more accurate (would likely want to override the file URL
                # with this since the file is directly attached). If no
                # archive_url is defined, set url to inf_url, as there's good
                # evidence this url is related to the file
                if not res.get('url'):
                    res['url'] = res['inf_url']

        # commented out for; extremely unlikely for a file to have a citekey but no
        # other source identifiers. If it does have a citekey, there are no instances
        # where I would want to overwrite listed files of links, in the case of a
        # (possible) duplicate entry. The other attrs should dictate the entry
        #if citekey and not res:
        #    res = bib_ent_by_citekey.get(citekey)

        # for downstream apps: bib data will provide url and inf_url. If url is
        # present, use it
        return res if res else {}


        

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
                tasklinks = '<button class="arrow ssrc" data-docsource="/simple/task-{id}">←</button>' + \
                            '<sup><a href="/task-{id}">+</a></sup>'
                s = s.replace(
                        m.group(5),
                        tasklinks.format(id=m.group(6).replace('  #',''))
                    )
            s = s.replace(m.group(6), '')
            return s

        nt = re.sub(
            pattern=r'\* (\[.\]) (.*?) ?(!{1,3})? ?(\(\d[^\)]*\))? ?(\+\+)?(  #\w{8})',
            repl=repl,
            string=string
        )

        return nt

    def transform_task_headers(self, string, op=False, remove=False):
        def repl(m):
            title = m.group(1)
            body  = m.group(3)
            opn   = 'open' if op else ''
            #gantt = task.taskdict_to_gantt_raw({
            #    title:
            #    task.get_tasks_from_ids(self.metadata['task_groups'].get(title))
            #})
            s = '<details class="tasks" {opn}>' + \
                    '<summary>{}</summary>' + \
                    '\n{}\n' + \
                '</details>'.format()
                #   '<details>' + \
                #       '<summary>Gantt view</summary>\n{gantt}\n' + \
                #   '</details>' + \

            #s = s.format(title, body, gantt=gantt)
            s = s.format(title, body, opn=opn)
            #s = '<details class="tasks"><summary>{}<hr class="solid"></summary>\n{}\n</details>'.format(title, body)
            return s

        nt = re.sub(
            pattern=r'#{1,6} (.*?) \| (.+)\n((?:.+(?:\n|$))*)',
            repl=repl if not remove else '',
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
            hash_src = tikz_src

            data_dir = '/home/smgr/Documents/notes/data'
            if hash_src.startswith('\\pgfplotstable'):
                hash_src += ''.join([Path(data_dir, f).open().read() 
                                     for f in utils.directory_tree(data_dir)])

            # generate stem filename from source hash
            svg_stem = utils.src_hash('livetex_', hash_src, '.svg')
            svg_full_path = str(Path(svg_full_prefix, svg_stem))
            svg_site_path = str(Path(svg_site_prefix, svg_stem))

            # convert tikz to svg
            # note: can safely ignore re-render since name is based on source hash
            if not Path(svg_full_path).exists():
                print(Fore.YELLOW + 'Rendering TikZ SVG {}'.format(svg_stem))
                utils.tex.tikz2svg(tikz_src, svg_full_path)

            return '![{}]({})'.format(caption, svg_site_path)

        nt = re.sub(
            pattern=r'!\[(.*?)\]\(\s*(\\begin{tikzpicture}.*?\\end{tikzpicture})\s*\)',
            repl=repl,
            string=string,
            flags=re.DOTALL
        )
        
        # try rendering anything(?) with a backslash in the caption
        # space, sufficiently rare; will reconsider on clash
        nt = re.sub(
            pattern=r'!\[(.*?)\]\(\s*(\\.*?)\s*\)',
            repl=repl,
            string=nt,
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
            #flags=re.DOTALL
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

            if Path('/home/smgr/Documents/notes/docs',stem).exists():
            #and stem.suffix != '.pdf':
                public_files[str(stem)] = str(Path('/docs/', stem))
             
            reg_src = Path('/home/smgr/Documents/notes/images/pdf/', stem)
            ann_src = Path('/home/smgr/Documents/notes/images/pdf/rm/docs/', stem)

            if reg_src.exists():
                public_carousel_str += self.carousel_html(str(stem), str(reg_src))
                #public_files[str(stem)] = str(Path('/docs/', stem))
            if ann_src.exists():
                name = 'rm/docs/'+str(stem)
                local_carousel_str += self.carousel_html(name, str(ann_src))
                local_files[name] = str(Path('/docs/', name))

        note_src = Path('/home/smgr/Documents/notes/images/pdf/rm/', self.name+'.pdf')
        if note_src.exists():
            name = 'rm/'+self.name+'.pdf'
            local_carousel_str += self.carousel_html(name, str(note_src))
            local_files[name] = str(Path('/docs/', name))

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
            pdoc_args.append('--toc-depth=4')

        self.html = {}
        self.html.update(self.metadata)
        
        # these should really become pandoc filters, move function pandocfilters filters
        # in regular location; can be location for all future modifiers (like tikz!)
        content = self.transform_links(self.content, graph=graph)
        content = self.transform_task_headers(content, remove=True)
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
                # test simply render; guess --embed-resources not an option? despite being
                # in the docs
                #self.html['simple_content'] = self.conversion_wrapper(
                #        content,
                #        extra_args=pdoc_args+['--embed-resources'],
                #        filters=filters
                #)

        except RuntimeError:
            print(Fore.RED + 'Pandoc failed to convert content in file '+ self.name)
            raise


        # non-body pdoc args, manual for now
        mmd_args = [
            '-C',
            '--bibliography={}'.format('/home/smgr/Documents/notes/docs/docsyncbib.bib'),
            '-M link-citations',
            '-M link-bibliography', 
        ]

        # convert backlinks
        for linklist in self.linkdata.values():
            for link in linklist:
                context = self.transform_links(link['context'])
                context = self.transform_tikz(context)
                context = self.transform_pdftex(context)
                context += '\n'+self.metadata['reflinks'] if self.metadata.get('reflinks') else ''
                if fast:
                    link['html'] = misaka.html(context)
                else:
                    link['html'] = self.conversion_wrapper(context, 
                                                           extra_args=mmd_args,
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
                                                        extra_args=mmd_args,
                                                        filters=filters)
                
                self.html[key] = re.sub(
                    pattern=r'^<p>(.*)</p>$',
                    repl=lambda m: m.group(1),
                    string=html_text,
                    flags=re.DOTALL
                )
