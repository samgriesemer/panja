from panja import Panja

OPTIONS = {
    'sitename': 'samgriesemer',
}

if __name__ == '__main__':
    site = Panja(
        'test/content',
        'test/output',
        'test/notes',
        'test/theme'
    )
    site.create_site()
