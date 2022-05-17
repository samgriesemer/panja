import sqlite3

SITEDATA_DB = '/home/smgr/.local/share/panja/sitedata.sqlite'

def dict2keys(di):
    if di is None: return []

    if type(di) in [str, int, float]:
        return [('',di)]
    
    out = []
    if type(di) is dict:
        for key, val in di.items():
            out += [(key+'.'+e[0],e[1]) for e in dict2keys(val)]
    if type(di) is list:
        for e in di:
            out += dict2keys(e)
    return out

def bulk_insert(triples):
    con = sqlite3.connect(SITEDATA_DB)

    query = '''insert into sitedata values (?, ?, ?)
               on conflict (dt, attr)
               do update set val=excluded.val'''

    # auto-commit w/o exception, else auto-rollback
    try:
        with con:
            con.executemany(query, triples)
    except sqlite3.IntegrityError:
        print('Error in bulk insert')

    con.close()
