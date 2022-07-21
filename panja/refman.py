import glob
from pathlib import Path
from tqdm import tqdm
import json
from typing import Optional, List

ARCHIVE_PATH = '/media/smgr/data/archivebox/archive'
# archived sites @ <timestamp>/index.json
    
class ArchiveEntry:
    def __init__(self, index_path):
        entry_file = Path(index_path)
        self.metadata = json.load(entry_file.open())

class Archive:
    def __init__(self, archive_path):
        self.entries = []

        for entry in tqdm(glob.glob(str(Path(archive_path, 'archive','*', 'index.json')))):
            ae = ArchiveEntry(entry)
            self.add_entry(ae)

    def add_entry(self, entry: ArchiveEntry):
        self.entries.append(entry)

    def by_tag(self, tag):
        results = []
        for entry in self.entries:
            if tag in entry.metadata.get('tags_str','').split(','):
                results.append(entry)
        return results

    @staticmethod
    def entries_to_links(entries: List):
        return [ 
            { 
              d: e.metadata.get(d)
              for d in ['title', 'url', 'timestamp', 'archive_path']
            }
            for e in entries
        ]


if __name__ == '__main__':
    archive = Archive(ARCHIVE_PATH)
    unread = archive.by_tag('')
    archive.entries_to_links(unread)
