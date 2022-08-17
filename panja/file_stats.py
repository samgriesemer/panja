from pathlib import Path
import glob
import subprocess
import re
from collections import defaultdict
from tqdm import tqdm
from difflib import unified_diff, HtmlDiff
from datetime import datetime
from typing import Optional

from panja.cache import Cache
from panja.article import Article
from panja import utils


class IncrementFile:
    """Diff-based stats for file groups"""
    link_regex = re.compile('\[\[([^\]]*?)(#[^\]]*?)?(?:\|([^\]]*?))?\]\]')
    reflink_regex = re.compile('\[(\w*)\]: (http[^\s]*) ?(?:\(([^\)]*)\))?')
    heading_regex = re.compile('(#{1,6}) (.*)')

    snp_list = ['.snapshot', '.snapshot.gz']
    dif_list = ['.diff', '.diff.gz']

    @classmethod
    def parse_event(cls, path):
        if Path(path).suffix == '.missing':
            return 'missing'
        elif any([str(Path(path)).endswith(s) for s in cls.snp_list]):
            return 'snapshot'
        elif any([str(Path(path)).endswith(s) for s in cls.dif_list]):
            return 'diff'
        return 'none'

    def __init__(self, inc_root, path):
        self.inc_root  = Path(inc_root)
        self.path      = Path(path)
        self.inc_regex = re.compile(r'{}/(.*)\.md\.\D*(.*?)\..*'.format(str(self.inc_root)))
        self.event     = self.parse_event(path)

        m = self.inc_regex.match(str(self.path))
        if m is not None:
            self.name, self.date = m.groups()
        else:
            self.name = self.date = ''

        self.restore_path = None
        self.post_bu_time = ''
        self.post_bu_diff = ''
        self.lines        = []
        self.stats        = {}
        self.wlinks       = {}

    def restore(self, tmp_path):
        # skip restore for missing (we know the outcome) and static (where a
        # existing file location has already been assigned)
        if self.event == 'missing' or self.event == 'static': return None

        # define restore_path if path exists or will be restored 
        self.restore_path = Path(
            tmp_path,
            '{}.md.{}.md'.format(self.name, self.date)
        )

        if self.restore_path.is_dir():
            self.restore_path.rmdir()

        if self.restore_path.exists():
            return None

        return subprocess.Popen([
            'rdiff-backup',
            self.path,
            self.restore_path
        ])

    def read_restore(self):
        if not self.lines:
            if self.restore_path is not None:
                with self.restore_path.open() as f:
                    self.lines = f.readlines()
            else:
                self.lines = []
        return self.lines

    def compute_stats(self):
        lstr = ''.join(self.lines)
        self.stats.update({
            'lines' : len(self.lines),
            'words' : len(lstr.split()),
            'links' : len(self.link_regex.findall(lstr)),
            'reflinks' : len(self.reflink_regex.findall(lstr)),
            'headings' : len(self.heading_regex.findall(lstr)),
            'files' : 0 if self.event == 'missing' else 1,
        })
        self.wlinks = Article.process_links(None, lstr)

    def set_post_bu_time(self, dt):
        if self.date and dt > self.date:
            self.post_bu_time = dt
            d2 = datetime.fromisoformat(dt)
            d1 = datetime.fromisoformat(self.date)
            self.post_bu_diff = round((d2-d1).total_seconds()/60)


class IncrementDiff:
    '''
    Intended usage: `inc_post` is an increment file representing a change captured by
    rdiff on the closest backup date following `inc_pre`. In this case:

    - the restored file content from `inc_post` represents the file's state from the
      pre-date up to the post-date; recall that increments are effectively reverse diffs,
      restoring to a particular increment gives the file state just before the change was
      made
    - the restored file content from `inc_pre` provides file state up to the pre-date
    - the diff text represents the change made _at_ the pre-date
        + so for .missing pre's, this diff object captures what happened on the creation
          date. In this case restoring to pre provides file content up the its (creation)
          date, i.e. restores to nothing.
        + .snapshot pre's 
    - For tail diffs with @current post's: all is normal unless the pre is a snapshot.
      However, such a file shouldn't even exist in the @current directory. We thus expect
      to provide an empty IF object, in which case the proper reverse diff is maintained.
    '''
    html_diff = HtmlDiff(tabsize=4,wrapcolumn=1000)

    def __init__(self, inc_pre: IncrementFile, inc_post: IncrementFile):
        self.inc_pre    = inc_pre
        self.inc_post   = inc_post
        self.diff_text  = ''
        self.diff_table = ''
        self.date       = inc_pre.date
        self.stats      = {}
        self.wlinks     = {}

    def compute_diff_text(self):
        self.diff_text = ''.join(unified_diff(
            self.inc_pre.read_restore(),
            self.inc_post.read_restore(),
            fromfile='{}@{}'.format(self.inc_pre.name,self.inc_pre.date),
            tofile='{}@{}'.format(self.inc_post.name,self.inc_post.date),
        ))

    def compute_diff_table(self):
        post_int = self.inc_pre.post_bu_diff
        post_str = '(+{}m)'.format(post_int) if post_int else ''
        table = self.html_diff.make_table(
            self.inc_pre.read_restore(),
            self.inc_post.read_restore(),
            fromdesc='{}@{}{}'.format(self.inc_pre.name,self.inc_pre.date,post_str),
            todesc='{}@{}'.format(self.inc_post.name,self.inc_post.date),
            context=True,
            numlines=1,
        )
        self.diff_table = re.sub(pattern=r'nowrap="nowrap"', repl='', string=table)

    def compute_stats(self):
        self.inc_pre.compute_stats()
        self.inc_post.compute_stats()
        self.stats.update({
            k: v-self.inc_pre.stats[k]
            for k,v in self.inc_post.stats.items()
        })
        self.wlinks.update({
            k: v-self.inc_pre.wlinks[k]
            for k,v in self.inc_post.wlinks.items()
        })


class DiffStat:
    def __init__(self,
        backup_path,
        tmp_path='/var/tmp/rdiff-stat/',
        diff_cache: Optional[Cache]=None,
        verbose=False,
        earlier_paths: Optional[list]=None
    ):
        self.backup_path       = Path(backup_path)
        self.backup_data_path  = Path(self.backup_path, 'rdiff-backup-data')
        self.increment_path    = Path(self.backup_data_path, 'increments')
        self.tmp_path          = Path(tmp_path)
        self.diff_cache        = diff_cache.load() if diff_cache is not None else None
        self.group_size        = 16
        self.verbose           = verbose
        self.earlier_paths     = earlier_paths if earlier_paths else []
        self.earlier_inc_paths = []
        self.last_updated      = None
        
        if earlier_paths is not None:
            self.earlier_inc_paths  = [Path(p, 'rdiff-backup-data/increments') for p in earlier_paths]

        self.inc_dict    = defaultdict(list)
        self.diff_dict   = defaultdict(list)
        self.dated_diffs = defaultdict(list)

        # session metadata on all backup attempts
        self.sessions = {}
        self.sorted_session_dates = []

        # dated absolute stats on per-file basis
        self.local_stats       = defaultdict(dict)
        self.local_inter_stats = defaultdict(dict)
        
        # dated global system stats
        self.global_stats = defaultdict(lambda: defaultdict(int))
        
        # raw per-file traces, origin stats at -1 and diffs thereafter
        # very similar to diff_dict but with whole system. Any files of
        # interest can just be plucked out and summed up together as
        # needed to get accurate stats while flattening all dates
        self.file_traces = defaultdict(dict)
        self.link_traces = defaultdict(dict)
        
        # create temp restore dir if needed
        self.tmp_path.mkdir(exist_ok=True)
        self.back_regex = re.compile(r'{}/(.*)\.md'.format(str(self.backup_path)))

    def process_sessions(self):
        for inc_path in self.earlier_paths+[self.backup_path]:
            bud_path = Path(inc_path, 'rdiff-backup-data')
            sessions = Path(bud_path, 'session_statistics.[0-9]*')
            sess_regex = re.compile(r'{}/session_statistics\.(.*)\.data'.format(bud_path))
            for i,session_path in enumerate(tqdm(glob.glob(str(sessions)),
                                    desc='process session files')):
                m = sess_regex.match(session_path)
                if not m: continue
                self.sessions[m.groups()[0]] = session_path

        self.sorted_session_dates = sorted(self.sessions.keys())

    def process_increments(self):
        wait_group = []

        # PROCESS MD RESTORATIONS
        for inc_path in self.earlier_inc_paths+[self.increment_path]:
            for i,increment in enumerate(tqdm(glob.glob(str(Path(inc_path, '*.md.[0-9]*'))),
                                    desc='restore MD archives')):
                fs = IncrementFile(inc_path, increment)
                
                # set nearest backup time following increment
                sess_loc = utils.bs(self.sorted_session_dates, fs.date)
                sess_len = len(self.sorted_session_dates)
                if sess_loc < sess_len:
                    if self.sorted_session_dates[sess_loc] == fs.date and sess_loc < sess_len-1:
                        sess_loc += 1
                    fs.set_post_bu_time(self.sorted_session_dates[sess_loc])

                self.inc_dict[fs.name].append(fs)

                rproc = fs.restore(self.tmp_path)
                if rproc is None:
                    if self.verbose:
                        print('Skipping {}@{}.{}'.format(fs.name,fs.date,fs.event))
                    continue
                else:
                    wait_group.append(rproc)

                # wait for group processes
                if len(wait_group) >= self.group_size:
                    print('file {}'.format(i))
                    exits = [p.wait() for p in wait_group]
                    wait_group = []

        # wait on any last processes
        exits = [p.wait() for p in wait_group]


        # COMPUTE MD DIFFS
        for fname, datelist in tqdm(self.inc_dict.items(),
                                    desc='compute full diff history'):
            datelist.sort(key=lambda x: x.date)
            f1d = datelist[0]

            for f2d in datelist[1:]:
                inc_diff = IncrementDiff(f1d, f2d)
                inc_diff.compute_diff_text()
                inc_diff.compute_diff_table()

                self.diff_dict[fname].append(inc_diff)
                f1d = f2d

            # create current increment file as tail
            f2d      = IncrementFile('','')
            f2d.name = fname
            f2d.date = 'latest'

            if f1d.event == 'snapshot':
                # if last event is snapshot, create contrived missing `latest` increment.
                # logically consistent with processing as stats represent state prior to
                # listed date; file is missing all the way up to @latest. there will
                # further be no later increments (this is @latest) and thus no diff
                # computed _through_ this increment (by definition impossible by date).
                f2d.event = 'missing'
            else:
                # other call event `static` and set the `restore_path`, which should
                # always exist if the last event is not a snapshot. restoring this event
                # will do nothing, but reading to get content at the path as expected.
                f2d.event        = 'static'
                f2d.restore_path = Path(str(Path(self.backup_path, fname))+'.md')

            inc_diff = IncrementDiff(f1d, f2d)
            self.diff_dict[fname].append(inc_diff)
            
            # otherwise compute final diff to current file state
            inc_diff.compute_diff_text()
            inc_diff.compute_diff_table()

    def compute_stats(self):
        # GLOBAL STAT COMPUTATION

        for fname, difflist in tqdm(self.diff_dict.items(),
                                    desc='compute local file stats'):
            
            # place absolute stats one date shifted earlier. since stats at inc_pre
            # give state up to but not including inc_pre.date, we want inc_pre.date to
            # to tell us stats happening _after_ the diff there. so we assign the next
            # stats in the chain to that last date
            last_date = '-1'
            difflist[0].compute_stats()
            self.file_traces[fname]['-1'] = difflist[0].inc_pre.stats
            self.link_traces[fname]['-1'] = difflist[0].inc_pre.wlinks

            for i, diff in enumerate(difflist):
                diff.compute_stats()
                self.local_stats[fname][last_date] = diff.inc_pre.stats
                self.file_traces[fname][diff.date] = diff.stats
                self.link_traces[fname][diff.date] = diff.wlinks
                self.dated_diffs[diff.date].append(diff)
                last_date = diff.date
                
                
            # add the state stats _after_ the last inc_pre.date, i.e. the absolute stats
            # of the file's current representation. The last inc_pre considered in the loop
            # gives stats up to but not including inc_pre.date, and are assigned to the date
            # before it. this means we don't get the absolute stats for current, so we add it
            # using the last diff's inc_post
            self.local_stats[fname][last_date] = diff.inc_post.stats

            # we now also add the diff_dict base to global_stats, where we
            # need to add _all_ diff_dict, not just those in diff_dict and currently in 
            # the backup path. This ensures we get snapshots that were present back in early
            # dates but no longer available; their diffs will bring stats down if we don't
            # account for their origin here.
            self.global_stats['-1'] = {
                k: self.global_stats['-1'][k]+v
                for k,v in difflist[0].inc_pre.stats.items()
            }


        # add files not seen in increments (they don't change through the date range we've
        # been tracking), and the base stats from the first increment for each file in the
        # diff_dict. Everything after that point is a diff for those files, so we need
        # that baseline to start from

        # also note: the diff-based nature of global stats means we span from the 
        # "-1" origin event through to the current, no matter what it is; we capture the
        # latest diff for all files where the current set of notes was produced _through_
        # that diff. For local_stats, however, we are just using absolute computations, so
        # we only have up to that last increment date (i.e. the file state just before the
        # diff occurring at that time took place). So we need to incorporate one last data
        # point for the current state of the file
        for i,fpath in tqdm(enumerate(glob.glob(str(Path(self.backup_path, '*.md')))),
                            desc='create non-increment base'):
            fname = self.back_regex.match(fpath).groups()[0]
            if fname in self.diff_dict: continue

            bfile = IncrementFile('','')
            bfile.restore_path = Path(fpath)
            bfile.read_restore()
            bfile.compute_stats()

            self.local_stats[fname]['-1'] = bfile.stats
            self.file_traces[fname]['-1'] = bfile.stats
            self.link_traces[fname]['-1'] = bfile.wlinks

            self.global_stats['-1'] = {
                k: self.global_stats['-1'][k]+v
                for k,v in bfile.stats.items()
            }
            
            
        print('diff_dict size: {}'.format(len(self.diff_dict)))
        print('global stat: {}'.format(self.global_stats['-1']))


        # GLOBAL AGGREGATION
        last_date = '-1'
        for date in tqdm(sorted(self.dated_diffs.keys()),
                         desc='final global aggregation'):
            self.global_stats[date] = self.global_stats[last_date]
            
            for diff in self.dated_diffs[date]:
                self.global_stats[date] = {
                    k: diff.stats[k]+v
                    for k,v in self.global_stats[date].items()
                }
                
            last_date = date

        # timing
        self.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def compute_inter_stats(self):
        for fname in tqdm(self.link_traces.keys(),
                          desc='compute local inter file stats'):
            self.local_inter_stats[fname] = self.stitch_traces([
                {
                    date:{'linked_to':links.get(fname,0)}
                    for date, links in trace.items()
                    if fname in links
                }
                for trace in self.link_traces.values()
            ])
        #full_trace = self.stitch_traces(list(self.link_traces.values()))
        #for date, stats in tqdm(full_trace.items(),
        #                        desc='compute local inter file stats'):
        #    for fname, count in stats.items():
        #        self.local_inter_stats[fname][date] = {
        #            'linked_to': stats.get(fname,0)
        #        }


    @staticmethod
    def stitch_traces(trace_list):
        '''
        Flattens traces across provided selection into a singular stats timeline.

        trace_list: list of traces i.e. dated dictionaries of stats dicts
        '''
        timeline = defaultdict(lambda: defaultdict(int))
        datediff = defaultdict(list)
        for trace in trace_list:
            for date, stat in trace.items():
                datediff[date].append(stat)

        last_date = '-1'
        for date in sorted(datediff.keys()):
            timeline[date] = timeline[last_date]
            for stat in datediff[date]:
                temp = {**timeline[date]}
                temp.update({
                    k: timeline[date].get(k,0)+v
                    for k,v in stat.items()
                })
                timeline[date] = temp
            last_date = date

        return timeline


if __name__ == '__main__':
    backup_path = '/media/smgr/data/backups/arch_incremental/notes-rdiff/'

    stats = DiffStat(
        backup_path,
        tmp_path='/var/tmp/rdiff-stat',
        verbose=False,
        earlier_paths=[
            '/media/smgr/data/backups/arch_incremental/notes-rdiff-pre080322/',
            '/media/smgr/data/backups/arch_incremental/rdiff-notes-pre041022/',
            '/media/smgr/data/backups/arch_incremental/notes-rdiff-pre042622/',
        ]
    )
    stats.process_sessions()
    stats.process_increments()
    stats.compute_stats()
    stats.compute_inter_stats()

    stats_cache = Cache(
        'newstat_samg.com',
        '/home/smgr/.cache/panja/',
    )
    stats_cache.write(stats)
