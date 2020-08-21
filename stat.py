from staticjinja import Site


if __name__ == "__main__":
    site = Site.make_site()
    # enable automatic reloading
    site.render(use_reloader=True)

import os

from staticjinja import Site

# Custom MarkdownExtension
from extensions import MarkdownExtension


def get_post_contents(template):
    with open(template.filename) as f:
        return {'post': f.read()}


# compilation rule
def render_post(env, template, **kwargs):
    """Render a template as a post."""
    post_template = env.get_template("_post.html")
    head, tail = os.path.split(post_template.name)
    post_title, _ = tail.split('.')
    if head:
        out = "%s/%s.html" % (head, post_title)
        if not os.path.exists(head):
            os.makedirs(head)
    else:
        out = "%s.html" % (post_title, )
    post_template.stream(**kwargs).dump(out)


if __name__ == "__main__":
    site = Site.make_site(extensions=[
        MarkdownExtension,
    ], contexts=[
        ('.*.md', get_post_contents),
    ], rules=[
        ('.*.md', render_post),
    ])
    site.render(use_reloader=True)
