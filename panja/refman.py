import os
import re
import glob
import shutil
from pathlib import Path
from tqdm import tqdm
import json
from typing import Optional, List
from datetime import datetime
from subprocess import call, DEVNULL
from tempfile import mkdtemp
from tqdm import tqdm
from colorama import Fore
import logging

import pdf2bib
pdf2bib.config.set('verbose',False)

from panja import utils


ARCHIVE_PATH = '/media/smgr/data/archivebox/archive'
# archived sites @ <timestamp>/index.json
    
class ArchiveEntry:
    def __init__(self, index_path):
        entry_file = Path(index_path)
        self.metadata = json.load(entry_file.open())

        # derivative metadata, could clash with vanilla properties
        ts = self.metadata.get('timestamp')
        
        if ts:
            self.metadata['datetime'] = datetime.fromtimestamp(float(ts)).isoformat()

class Archive:
    def __init__(self, archive_path):
        self.entries = []
        self.archive_path = archive_path
        self.refresh_entries()

    def refresh_entries(self):
        self.entries = []
        for entry in tqdm(glob.glob(str(Path(self.archive_path, 'archive','*', 'index.json')))):
            ae = ArchiveEntry(entry)
            self.add_entry(ae)

    def get_entries(self):
        return self.entries

    def add_entry(self, entry: ArchiveEntry):
        self.entries.append(entry)

    def by_tag(self, tag):
        results = []
        for entry in self.entries:
            if tag in entry.metadata.get('tags_str','').split(','):
                results.append(entry)
        return results

    def by_attr(self, **kwargs):
        '''
        Filter entries by attributes.

        `attr_pairs`: list of (attr_key,attr_val) pairs. `attr_val` can be a list of
                      acceptable values for the `attr_key`. Results are conjunction of
                      each entry-matching disjunction.
        '''
        results = []
        for entry in self.entries:
            addflag = True
            for key, val in kwargs.items():
                entry_val = entry.metadata.get(key,None)
                if type(entry_val) is list:
                    if type(val) is list:
                        if not set(val).intersection(set(entry_val)):
                            addflag = False
                            break
                    else:
                        if val not in entry_val: 
                            addflag = False
                            break
                elif type(entry_val) is dict:
                    if type(val) is dict:
                        for k,v in val.items():
                            if type(v) is bool:
                                if bool(entry_val.get(k,False)) != v:
                                    addflag = False
                            elif entry_val.get(k) != v:
                                addflag = False
                else:
                    if type(val) is list:
                        if entry_val not in val:
                            addflag = False
                            break
                    else:
                        if entry_val != val:
                            addflag = False
                            break
            if addflag: results.append(entry)
        return results

    def get_links(self):
        return self.entries_to_links(self.entries)

    @staticmethod
    def entries_to_links(entries):
        return [ 
            { 
              d: e.metadata.get(d,'')
              for d in ['title', 'url', 'timestamp', 'datetime', 'archive_path']
            }
            for e in entries
        ]


class DocSync():
    '''
    Sync PDF documents to BibTeX entries. Handle renaming, citekey generation, metadata
    extraction, etc.

    A full sync might look like:
    ```
    ds = DocSync(path, bpath)
    ds.fix_duplicates()
    ds.rename_existing()
    ds.sync_to_bib()
    '''
    BIBTEX_ENTRY_REGEX = re.compile('^@.*{(.*),\n[\s\S]*?\n}',re.MULTILINE)
    BIBTEX_FILE_REGEX  = re.compile('^[^\S\r\n]*?file[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)
    BIBTEX_APATH_REGEX = re.compile('^[^\S\r\n]*?archive_path[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)
    BIBTEX_AURL_REGEX  = re.compile('^[^\S\r\n]*?archive_url[^\S\r\n]*?=[^\S\r\n]*?{(.*)}',re.MULTILINE)
    BIBTEX_TITLE_REGEX = re.compile('^[^\S\r\n]*?title[^\S\r\n]*?=[^\S\r\n]*?{(.*?)}',re.MULTILINE|re.DOTALL)

    def __init__(self, pdf_path, bib_path):
        self.pdf_path = Path(pdf_path).expanduser().resolve()
        self.bib_path = Path(bib_path).expanduser().resolve()
        self.blk_path = Path(self.bib_path.parents[0], 'docsync.blacklist')

        self.bib_entries = {}
        self.bib_entries_by_file = {}
        self.bib_entries_by_apath = {}
        self.bib_file2key = {}

        self.blk_entries = set()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False # may help with duplicate logging
        self.logger.addHandler(utils.TqdmLoggingHandler())

    def add_paper(self, filepath): pass

    def parse_bib(self):
        '''
        Note: the way this method is defined, duplicate bib entries will automatically be
        removed (overwritten citekeys in the `bib_entries` dict). There could be some
        issues with this with accidental citekey collisions. If the bib file had these
        duplicate citekeys, it would already be presenting some issues in the first place,
        so this isn't too much of an issue for now. But syncing processes should ensure
        they aren't writing duplicate keys; otherwise, the bib can change between two
        syncs even without any files changing on disk.
        '''
        self.bib_path.touch(exist_ok=True)
        self.bib_entries = {}
        self.bib_entries_by_file = {}
        self.bib_entries_by_apath = {}
        self.bib_entries_by_aurl = {}
        self.bib_file2key = {}

        bib_content = self.bib_path.open().read()
        for m in self.BIBTEX_ENTRY_REGEX.finditer(bib_content):
            self.bib_entries[m.group(1)] = m.group(0)

            file_attr = self.BIBTEX_FILE_REGEX.search(m.group(0))
            if file_attr:
                self.bib_entries_by_file[str(Path(file_attr.group(1)))] = m.group(0)
                self.bib_file2key[str(Path(file_attr.group(1)))] = m.group(1)

            archive_path_attr = self.BIBTEX_APATH_REGEX.search(m.group(0))
            if archive_path_attr:
                self.bib_entries_by_apath[str(Path(archive_path_attr.group(1)))] = m.group(0)

            archive_url_attr = self.BIBTEX_AURL_REGEX.search(m.group(0))
            if archive_url_attr:
                self.bib_entries_by_aurl[archive_url_attr.group(1)] = m.group(0)

        # parse blacklist
        self.blk_path.touch(exist_ok=True)
        self.blk_entries = set()
        blk_content = self.blk_path.open().readlines()
        self.blk_entries = set(map(lambda x:x.strip(), blk_content))


    def sync_to_bib(self, recursive=False, delete=False, rename=False, ignorepaths=None):
        '''
        Sync BibTeX entries for *.pdf files in path to `bibfile`. Queries metadata for
        files that aren't yet stored, ignores those that are, and deletes entries for
        which no file exists (if optional delete is set to True).

        Handles unique citekey assignment for new PDFs not yet synced. By design does not
        attempt to correct any pre-existing entries (which may have somehow been assigned
        the same citekey in past, regardless of whether they are duplicate files). The
        `rename` parameter also only applies to new entries; changing existing entries is
        handled explicitly, outside this method.

        Note: entries with duplicate citekeys will naturally be removed (all but one)
        during the method call. We will recognize each duplicate as an existing entry, but
        during the final BibTeX rewrite, we only write unique keys (`pre_entries` is
        defined using `self.bib_entries`, whereas the check for existence uses
        `self.bib_entries_by_file`). Hence, given any two syncs, there will be no
        duplicate keys (barring other changes).
        '''
        self.parse_bib()
        pdf_glob = Path(self.pdf_path,'**/*.pdf') if recursive else Path(self.pdf_path,'*.pdf')

        black_list = []
        add_entries = []
        pre_entries = list(self.bib_entries.values()) if not delete else []
        running_citekeys = set(self.bib_entries.keys())
        ignorepaths = ignorepaths if ignorepaths else []

        for pdf in tqdm(glob.glob(str(pdf_glob), recursive=recursive),
                        desc='docsync: syncing {} to BibTeX'.format(self.pdf_path),
                        colour='cyan'):
            
            # consistent repr of PDF path; matching is sensitive
            pdf_path = str(Path(pdf))
            entry_str = ' entry: {}'.format(pdf_path)

            # handle existing entries
            if pdf_path in self.bib_entries_by_file:
                self.logger.info(utils.color_str('[existing]',Fore.YELLOW)+entry_str)
                if delete:
                    pre_entries.append(self.bib_entries_by_file[pdf_path])

            elif pdf_path in self.blk_entries:
                self.logger.info(utils.color_str('[blacklisted]',Fore.BLACK)+entry_str)
                continue

            else:
                if any([Path(pdf_path).is_relative_to(ip) for ip in ignorepaths]):
                    self.logger.info(utils.color_str('[ignored]', Fore.YELLOW)+entry_str)
                    black_list.append(pdf_path)
                    continue


                # PDF not yet seen, attempt to resolve
                res = pdf2bib.pdf2bib(pdf_path)

                if res is None or res.get('metadata') is None:
                    self.logger.info(utils.color_str('[failed]', Fore.RED)+entry_str)
                    black_list.append(pdf_path)
                    continue
                else:
                    self.logger.info(utils.color_str('[new]',Fore.GREEN)+entry_str)

                citekey = self.get_clean_key_from_bibtex(res['bibtex'])
                if citekey in running_citekeys:
                    self.logger.info(utils.color_str('[citekey clash]',Fore.YELLOW)+entry_str)

                    # assign unique citekey
                    while citekey in running_citekeys:
                        citekey = self.increment_citekey(citekey)

                rename_path = Path(self.pdf_path, citekey).with_suffix('.pdf')
                if rename and pdf_path != str(rename_path):
                    if self.rename_file(pdf_path, rename_path):
                        pdf_path = rename_path

                res['metadata']['file'] = pdf_path
                bibtex = pdf2bib.make_bibtex(res['metadata'])
                bibtex = self.replace_bibtex_citekey(bibtex, citekey)

                running_citekeys.add(citekey)
                add_entries.append(bibtex)

        # rewrite bib
        self.rewrite_bib(add_entries+pre_entries)
        self.append_blk(black_list)

    def sync_from_archive(self, archive, rename=False):
        '''
        Pull (new) PDF sources from an Archive, copy them to the PDF path, rename
        according to citekey. Maintains archive-added entries with extra BibTeX metadata
        to enable proper association during syncing.

        Note: as is, renaming only applies to new sources not already copied (ie with a
        unique path on disk). Although each sync operates on all files from the archive,
        those that have been copied need to be renamed using another operation.
        '''
        self.parse_bib()
        new_entries = []
        black_list = []
        running_citekeys = set(self.bib_entries.keys())
        archived_pdfs = archive.by_attr(extension='pdf',is_archived=True)

        for entry in tqdm(archived_pdfs,
                          desc='syncing archive to {}'.format(self.pdf_path),
                          colour='magenta'):
            entry_pdf_path = str(Path(
                archive.archive_path,
                entry.metadata['archive_path'],
                entry.metadata['canonical']['pdf_path']
            ))
            
            # skip if entry already represented
            if entry_pdf_path in self.bib_entries_by_apath: 
                self.logger.info(
                    utils.color_str('[existing]',Fore.YELLOW) +
                    'entry URL: {}'.format(entry.metadata.get('url'))
                )
                continue

            # check if vanilla move path in blacklist. This is good enough because files
            # that don't have valid entries don't get renamed, so we don't need to worry
            # about any other possible name.
            proposal_path = Path(self.pdf_path, Path(entry_pdf_path).name)
            if proposal_path in self.blk_entries:
                continue

            # copy pdf file to pdf_path
            if proposal_path.is_file():
                self.logger.info(
                    utils.color_str('[duplicate filename]',Fore.RED) +
                    'NOT COPYING entry URL: {}'.format(entry.metadata.get('url'))
                )
                continue
            else:
                pdf_path = shutil.copy(entry_pdf_path, self.pdf_path)
            
            # GENERATE BIBTEX
            res = pdf2bib.pdf2bib(pdf_path)
            if res is None or res.get('metadata') is None:
                self.logger.info(utils.color_str('pdf2bib failing on file {}, skipping'.format(pdf_path),Fore.RED))
                black_list.append(pdf_path)
                continue
            else:
                self.logger.info(utils.color_str('[new]',Fore.GREEN)+'entry URL: {}'.format(entry.metadata.get('url')))
            
            # GENERATE CITEKEY
            citekey = self.get_clean_key_from_bibtex(res['bibtex'])
            if citekey in running_citekeys:
                self.logger.info(utils.color_str('[citekey clash]',Fore.YELLOW)+'entry URL: {}'.format(entry.metadata.get('url')))
            
                # assign unique citekey
                while citekey in running_citekeys:
                    citekey = self.increment_citekey(citekey)

            # RENAME TO CITEKEY
            rename_path = Path(self.pdf_path, citekey).with_suffix('.pdf')
            if rename and pdf_path != str(rename_path):
                if self.rename_file(pdf_path, rename_path):
                    pdf_path = rename_path

            res['metadata']['archive_path'] = entry_pdf_path
            res['metadata']['archive_url']  = entry.metadata.get('url')
            res['metadata']['file']         = pdf_path

            bibtex = pdf2bib.make_bibtex(res['metadata'])
            bibtex = self.replace_bibtex_citekey(bibtex, citekey)

            running_citekeys.add(citekey)
            new_entries.append(bibtex)

        self.prepend_bib(new_entries)

    def rename_existing(self): pass

    def increment_citekey(self, citekey):
        tail = re.search(r'_(\w)$', citekey)
        if tail is None:
            return citekey+'_a'
        else:
            return re.sub(r'_(\w)$', lambda c:'_'+chr(ord(c.group(1))+1), citekey)

    def replace_bibtex_citekey(self, bibtex, citekey):
        def repl(m):
            etype = m.group(1)
            return '@{}{{{},'.format(etype,citekey)

        return re.sub(
            r'@(.*)\{(.*),',
            repl,
            bibtex
        )

    def clean_key(self, key):
        return ''.join(c for c in key if c.isalnum() or c=='_')

    def get_clean_key_from_bibtex(self, bibtex):
        m = self.BIBTEX_ENTRY_REGEX.search(bibtex)
        if m is None:
            self.logger.info('clean_key: failed to recognize bibtex')
            return None
        elif not m.group(1):
            self.logger.info('clean_key: failed to identify key')
            return None
        else:
            return self.clean_key(m.group(1))
        

    def rename_file(self, oldpath, newpath):
        npath = Path(newpath)
        opath = Path(oldpath)
        if npath.is_file():
            self.logger.info(
                utils.color_str('renaming {} failed, {} exists'.format(oldpath, newpath),Fore.RED)
            )
            return False
        else:
            self.logger.info(
                utils.color_str('successful rename from {} to {}'.format(oldpath, newpath),Fore.GREEN)
            )
            opath.rename(npath)
            return True

    def rewrite_bib(self, entries):
        if entries:
            self.bib_path.write_text('\n\n'.join(entries))
            self.parse_bib()

    def prepend_bib(self, new_entries):
        self.parse_bib()
        pre_entries = list(self.bib_entries.values())
        self.rewrite_bib(new_entries+pre_entries)

    def append_blk(self, entries):
        if entries:
            self.blk_path.write_text('\n'.join(list(self.blk_entries)+entries))
            self.parse_bib()


class RMCache:
    '''
    Wrapper class for pulling, converting, and moving rM documents.

    Note: do not include prefix fslash on `from_path`.
    Note2: sync applies to directory structure _inside_ the `from_path`. The outer
           most folder is not preserved. e.g. `sync_from_path/*` is synced to
           `sync_to_path/*`
    '''
    def __init__(self,
        #temp_path='~/.cache/rm/',
        sync_from_path,
        sync_to_path,
        cache_path='~/.cache/rmapi/',
        file_list=None,
    ):
        self.sync_from_path = Path(sync_from_path).expanduser()
        self.sync_to_path = Path(sync_to_path).expanduser()
        self.cache_path = Path(cache_path).expanduser()
        self.tree = {}
        self.id2dir = {}
        self.file_list = file_list if file_list else []

    def refresh_tree(self):
        call(['rmapi', 'exit'],stdout=DEVNULL,stderr=DEVNULL)
        self.tree = json.load(Path(self.cache_path, '.tree').open())

        dir_cache = {}
        id2name = {}
        for e in self.tree['Docs']:
            dir_cache[e['DocumentID']] = e['Metadata']['parent']
            id2name[e['DocumentID']] = e['Metadata']['visibleName']

        id2dir = {}
        for did, par in dir_cache.items():
            dpath = Path(id2name[did])
            while par and par != 'trash':
                if par in id2dir:
                    dpath = Path(id2dir[par],dpath)
                    break
                dpath = Path(id2name[par],dpath)
                par = dir_cache[par]
            id2dir[did] = dpath
        self.id2dir = id2dir

    def sync(self):
        '''
        Sync files found on rM with the output directory. Modified times
        are compared between locations; files with last_modified times
        more recent than the associated copy in the outdir are replaced.

        Seems to take a variable amount of time for mod times to actually sync
        to rM servers and/or `rmapi` to grab theme. Up to a few minutes based on
        experience
        '''
        tmpdir = mkdtemp()
        os.chdir(tmpdir)
        self.refresh_tree()
        print('Syncing "{}" to "{}"'.format(self.sync_from_path,self.sync_to_path))

        for e in tqdm(self.tree['Docs']):
            name = e['Metadata']['visibleName']
            rm_modtime = float(e['Metadata']['lastModified'])
            rm_path = self.id2dir[e['DocumentID']]
            rm_dir = rm_path.parents[0]
            rm_pdf = Path(name+'.pdf')
            rm_zip = Path(name+'.zip')
            
            if self.file_list:
                if str(rm_path) in self.file_list:
                    fpath = Path(self.sync_to_path, rm_pdf)
                    print('Found in file list: {} to {}'.format(rm_path,fpath))
                else: continue
            else:
                if not rm_dir.is_relative_to(self.sync_from_path): continue
                rm_rel = rm_dir.relative_to(self.sync_from_path)
                fpath  = Path(self.sync_to_path, rm_rel, rm_pdf)
                print('Found in std recursive: {} to {}'.format(rm_path,fpath))

            if not fpath.is_file() or rm_modtime > fpath.stat().st_mtime*1000:
                call(['rmapi','get',rm_path],stdout=DEVNULL,stderr=DEVNULL)
                
                if not rm_zip.exists():
                    print('{} expected, not found during download'.format(rm_zip))
                
                fpath.parents[0].mkdir(parents=True, exist_ok=True)

                # can be replaced with rmrl python api if needed
                call(['python','-m','rmrl',rm_zip,fpath],stdout=DEVNULL)



if __name__ == '__main__':
    #archive = Archive(ARCHIVE_PATH)
    #unread = archive.by_tag('')
    #archive.entries_to_links(unread)
    RMCache('notes','~/Documents/notes/docs/rm').sync()
    RMCache('','~/Documents/notes/docs/rm/root',file_list=['Quick sheets','dTODO','ideas']).sync()
