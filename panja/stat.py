from pathlib import Path
import glob
import subprocess
import re
from collections import defaultdict
from tqdm import tqdm
from difflib import unified_diff, HtmlDiff

backup_location = '/media/smgr/data/backups/arch_incremental/notes-rdiff/'
increment_subdir = 'rdiff-backup-data/increments'
temp_restore_dir = '/var/tmp/rdiff-stat/'
rdiff_cmd = 'rdiff-backup {} {}'
increments_path = Path(backup_location, increment_subdir)

# create temp dir
Path(temp_restore_dir).mkdir(exist_ok=True)
inc_regex = re.compile(r'{}/(.*)\.md\.(.*?)\..*'.format(str(increments_path)))
bak_regex = re.compile(r'{}/(.*)\.md'.format(str(Path(backup_location))))

inc_trace = defaultdict(list)

# set large col number to prevent forced nowrap
html_diff = HtmlDiff(tabsize=4,wrapcolumn=1000)
link_regex = re.compile(r'\[\[([^\]]*?)(#[^\]]*?)?(?:\|([^\]]*?))?\]\]')

group_size = 16
wait_group = []

def data_from_increment(increment_path):
    '''
    Return filename and date from increment path
    '''
    return inc_regex.match(increment_path).groups()

def restore_path(fname, fdate):
    temp_filename = '{}.md.{}.md'.format(fname, fdate)
    return Path(temp_restore_dir, temp_filename)

def inc_lines(fname, fd):
    if fd['event'] == 'missing':
        return []
    
    with restore_path(fname, fd['date']).open() as f:
        return f.readlines()

def get_current_lines(fname):
    path = Path(str(Path(backup_location, fname))+'.md')
    with path.open() as f:
        return f.readlines()

def compute_diff(fname, f1d, f2d):
    return unified_diff(
        f1d['lines'], f2d['lines'],
        fromfile='{}@{}'.format(fname,f1d['date']),
        tofile='{}@{}'.format(fname,f2d['date']),
    )

def make_diff_table(fname, f1d, f2d):
    table = html_diff.make_table(
        f1d['lines'], f2d['lines'],
        fromdesc='{}@{}'.format(fname,f1d['date']),
        todesc='{}@{}'.format(fname,f2d['date']),
        context=True,
        numlines=1,
    )
    return re.sub(pattern=r'nowrap="nowrap"', repl='', string=table)


# PROCESS MD RESTORATIONS
for i,increment in tqdm(enumerate(glob.glob(str(Path(increments_path, '*.md.*'))))):
    # data from increment file
    fname, fdate = data_from_increment(increment)

    fd = {'date':fdate}
    snp_list = ['.snapshot', '.snapshot.gz']
    dif_list = ['.diff', '.diff.gz']

    if Path(increment).suffix == '.missing':
        # record missing file
        fd.update({'event':'missing'})
    elif any([str(Path(increment)).endswith(s) for s in snp_list]):
        # record snapshot file
        fd.update({'event':'snapshot'})
    elif any([str(Path(increment)).endswith(s) for s in dif_list]):
        # otherwise record regular diff
        fd.update({'event':'diff'})

    inc_trace[fname].append(fd)

    # skip if missing file
    if Path(increment).suffix == '.missing': continue

    # clean if broken (i.e. endpoint halted at dir)
    outpath = restore_path(fname, fdate)
    if outpath.is_dir(): outpath.rmdir()

    # skip if already processed
    if outpath.exists():
        print('Skipping {}@{}'.format(fname,fdate))
        continue

    # restore pre-diff file using rdiff
    proc = subprocess.Popen(rdiff_cmd.format(
        increment,
        str(outpath)
    ).split(' '))
    wait_group.append(proc)

    # wait for group processes
    if i > 0 and len(wait_group) >= group_size:
        print('file {}'.format(i))
        exits = [p.wait() for p in wait_group]
        wait_group = []

# wait on any last processes
exits = [p.wait() for p in wait_group]


# COMPUTE MD DIFFS
for fname, datelist in tqdm(inc_trace.items()):
    datelist.sort(key=lambda x: x['date'])
    f1d=f2d=None
    dated_diffs = {}

    f1d = datelist[0]
    f1d.update({'lines':inc_lines(fname, f1d)})

    for f2d in datelist[1:]:
        f2d.update({'lines':inc_lines(fname, f2d)})

        diff = compute_diff(fname, f1d, f2d)
        html_table = make_diff_table(fname, f1d, f2d)
        f1d.update({
            'diff': ''.join(diff),
            'html_table': html_table
        })
        f1d = f2d

    # if last event is snapshot, diff already computed
    if f1d['event'] == 'snapshot':
        f2d = {
            'date': 'current',
            'event': 'static',
            'lines': []
        }
        datelist.append(f2d)
        continue
    
    # compute final diff to current file state
    f2d = {
        'date': 'current',
        'event': 'static',
        'lines': get_current_lines(fname)
    }
    datelist.append(f2d)

    diff = compute_diff(fname, f1d, f2d)
    html_table = make_diff_table(fname, f1d, f2d)
    f1d.update({
        'diff': ''.join(diff),
        'html_table': html_table
    })
        
# GLOBAL STAT COMPUTATION
local_stats = {}
global_stats = defaultdict(list)
for fname, datelist in tqdm(inc_trace.items()):
    file_stats = {}
    last_line_count = 0
    last_word_count = 0
    last_link_count = 0
    for i,fd in enumerate(datelist):
        abs_line_count = len(fd['lines'])
        abs_word_count = len(''.join(fd['lines']).split())
        abs_link_count = len(link_regex.findall(''.join(fd['lines'])))

        diff_line_count = abs_line_count-last_line_count
        diff_word_count = abs_word_count-last_word_count
        diff_link_count = abs_link_count-last_link_count
        # link_count TBI

        stat = {
            'lines': abs_line_count,
            'words': abs_word_count,
            'links': abs_link_count,
            'files': 0
        }

        statd = {
            'lines': diff_line_count,
            'words': diff_word_count,
            'links': diff_link_count,
            'files': 0
        }

        if i == 0:
            if fd['event'] != 'missing':
                stat['files'] = 1
                statd['files'] = 1

            file_stats['-1'] = stat
            global_stats['-1'].append(statd)
        else:
            if datelist[i-1]['event'] == 'missing':
                stat['files'] = 1
                statd['files'] = 1
            elif datelist[i-1]['event'] == 'snapshot':
                stat['files'] = -1
                statd['files'] = -1
            file_stats[datelist[i-1]['date']] = stat
            global_stats[datelist[i-1]['date']].append(statd)

        last_line_count = abs_line_count
        last_word_count = abs_word_count
        last_link_count = abs_link_count
    local_stats[fname] = file_stats


# GLOBAL AGGREGATION
# need to compute from full base, not just files in increments
gstat = defaultdict(lambda: defaultdict(int))

# add files not seen in increments
inc_files = set(local_stats.keys())
for i,fpath in tqdm(enumerate(glob.glob(str(Path(backup_location, '*.md'))))):
    fname = bak_regex.match(fpath).groups()[0]
    if fname in inc_files: continue

    lines = get_current_lines(fname)
    temp_line_count = len(lines)
    temp_word_count = len(''.join(lines).split())
    temp_link_count = len(link_regex.findall(''.join(fd['lines'])))

    gstat['-1']['lines'] += temp_line_count
    gstat['-1']['words'] += temp_word_count
    gstat['-1']['links'] += temp_link_count
    gstat['-1']['files'] += 1

last_date = '-1'
for date in tqdm(sorted(global_stats.keys())):
    gstat[date]['lines'] = gstat[last_date]['lines']
    gstat[date]['words'] = gstat[last_date]['words']
    gstat[date]['files'] = gstat[last_date]['files']
    gstat[date]['links'] = gstat[last_date]['links']
    for stat in global_stats[date]:
        gstat[date]['lines'] += stat['lines']
        gstat[date]['words'] += stat['words']
        gstat[date]['files'] += stat['files']
        gstat[date]['links'] += stat['links']
    last_date = date


        
    
# lines at diff date represent the state of that file _up to that time_, i.e. just before
# the diff occurred. The diff lines represent the changes that took place _through_ that
# time. So the lines at a particular diff time were present in the system all the way back
# to the previous diff time, since the diff time itself represents a change to a new
# state.
# Thus, to accurately track changes globally, we simply need to shift all dates back by
# one increment. That is, the recorded file lines at the n^th increment should be dated
# according to the (n-1)^th increment, since the state of the file has been present only
# up to the date of that n^th increment. The first increment can just be shifted to some
# indicator value, so we know that's the earliest info we have for that file. This is fine
# even for mid-dated missing files.
    
    #re.split(r'---.*?\+\+\+.*?@@.*?@@',a+a,flags=re.DOTALL)

from panja.cache import Cache

stat_cache = Cache(
    'stat_samg.com_b',
    '/home/smgr/.cache/panja/',
)

obj = {
    'gstat': gstat,
    'global_stats': global_stats,
    'local_stats': local_stats,
    'inc_trace': inc_trace
}

stat_cache.write(obj)
