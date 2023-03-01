import sqlalchemy as sa
from pathlib import Path
from tqdm import tqdm
import os
from panja import cache

abs_db_path = Path("/home/smgr/.cache/panja/localsite.db").absolute()
engine = sa.create_engine(f"sqlite:///{abs_db_path}", echo=True)
meta = sa.MetaData()


# enable SQLite Foreign key constraints on both connection and executes; foreign keys do
# nothing by default b/c earlier SQLite versions didn't support
@sa.event.listens_for(sa.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# unique pages and select metadata
pages = sa.Table(
    "pages",
    meta,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, unique=True),
    sa.Column(
        "fullpath",
        sa.String,
        default="",
        unique=True,
    ),
    sa.Column("title", sa.String, default=""),
    sa.Column("type", sa.String, default=""),
)

# backlink block content; may not enforce Foreign Key? I can imagine blinks pushed out of
# order (or dynamically during page processing, meaning all pages aren't in before first
# blink). Plus it doesn't really matter if they're actual pages, links used to non-pages
# all the time.
blocks = sa.Table(
    "blocks",
    meta,
    # sa.Column('parent_page', sa.ForeignKey(pages.c.page), nullable=False),
    sa.Column("id",     sa.Integer, primary_key=True),
    sa.Column("ref_to", sa.String, nullable=False),
    sa.Column("ref_by", sa.String, nullable=False),
    sa.Column("context", sa.String, nullable=False),
    sa.Column("html", sa.String, default=""),
    sa.Column("line", sa.String, default=""),
    sa.Column("col", sa.String, default=""),
    sa.Column("header", sa.String, default=""),
    sa.Column("bounds", sa.String, default=""),
)


# will need separate tables for some of the many-to-many relationships in page metadata
# (e.g. tags, sources, files, etc). Obviously you can't stick arbitrary length attributes
# in columns of a table; they need to be rows of a new table. For tags, for example,
# each tag may be on many pages, and each page may have many tags. Traditionally, you'll
# need a Tags page with unique tag strings (and whatever else you might want for a tag
# object), and then an intermediate table that ties foreign keys from both Tags and Pages
# together. However I feel like you can get away without the explicit Tags table and just
# have something like a PageTags (intermediate) table that connects to Pages and but has
# arbitrary tags.

# for backlink use case, may not need even the Pages table. If planning positive or
# negative selectors, need to perform consecutive intersections, some additive some
# canceling


# GRAPH METHODS
def graph_to_pages(graph):
    with engine.connect() as connection:
        # for article in tqdm(graph.get_article_list(),desc='pages insert'):

        # INDIVIDUAL INSERTS PER ROW
        # for article in graph.get_article_list():
        #    connection.execute(
        #        pages.insert(),
        #        { **vars(article), **article.metadata }
        #    )

        # CHUNKED INSERT (IMPLICIT EXECUTEMANY); default params generated b/c all entries
        # must be the same. default_dict only defines values for those with specified
        # defaults in the table definition (local, not server_defaults)
        default_dict = pages.insert().values().compile().params
        connection.execute(
            sa.insert(pages),
            [
                {**default_dict, **vars(article), **article.metadata}
                for article in graph.get_article_list()
            ],
        )
        connection.commit()


def graph_to_blocks(graph):
    with engine.connect() as connection:
        default_dict = blocks.insert().values().compile().params
        connection.execute(
            sa.insert(blocks),
            [
                {
                    **default_dict,
                    **{k: str(v) for k, v in link.items()},
                    "ref_to": pn,
                    "ref_by": article.name,
                }
                for article in graph.get_article_list()
                for pn, linklist in article.linkdata.items()
                for link in linklist
            ],
        )
        connection.commit()


def create_fts5(
        table,
        engine,
        columns=None,
        populate=False,
        reset_fts=False,
        tokenizer='unicode61'
    ):
    table_name = table.name
    columns = [c.name for c in table.c] if columns is None else columns
    columns = ", ".join(columns)
    fts_table_name = f'{table_name}_fts_{tokenizer}'

    sql = f"""
    CREATE VIRTUAL TABLE {fts_table_name} USING fts5
    (
        {columns},
        tokenize = '{tokenizer}'
    );
    """

    sql_insert = f"""
    INSERT INTO {fts_table_name}
    (
        {columns}
    )
    SELECT {columns}
    FROM {table_name};
    """

    sql_drop = f"DROP TABLE IF EXISTS {fts_table_name}"

    with engine.connect() as connection:
        if reset_fts:
            connection.execute(sa.text(sql_drop))
        connection.execute(sa.text(sql))
        if populate:
            connection.execute(sa.text(sql_insert))
        connection.commit()


if __name__ == "__main__":
    import time

    # with engine.connect() as connection:
    # connection.execute(blocks.insert().values(parent_page='test7',content='hi!'))
    # connection.commit()
    # blocks.drop(engine)
    # pages.drop(engine)

    meta.drop_all(engine)
    meta.create_all(engine, checkfirst=True)

    print("Loading graph cache")
    cachepath = os.path.expanduser("~/.cache/panja/")
    graph_cache = cache.Cache(
        "graph_samg.com_bproto",
        cachepath,
    )
    graph = graph_cache.load()

    global_start = time.time()
    # create tables
    start = time.time()
    graph_to_pages(graph)
    print('Created table "pages"; took {}s'.format(time.time() - start))

    start = time.time()
    graph_to_blocks(graph)
    print('Created table "blocks"; took {}s'.format(time.time() - start))

    # create indexes
    start = time.time()
    tables_to_index = [pages, blocks]
    tokenizers = ['unicode61', 'porter', 'trigram']

    for table in tables_to_index:
        for tokenizer in tokenizers:
            create_fts5(table, engine, populate=True, reset_fts=True, tokenizer=tokenizer)

            print(f'Created FTS5 index for table "{table.name}+{tokenizer}"; took {time.time() - start}s')
            start = time.time()

    print("Total time: {}s".format(time.time() - global_start))
