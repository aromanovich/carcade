.. _example:
Example
=======

This is a very short example. You can find some more comprehensive examples here:
https://github.com/aromanovich/carcade-examples

Suppose project directory looks as follows:

  ::

    .
    ├── layouts
    │   ├── _base.html
    │   └── page.html
    ├── pages
    │   ├── four
    │   │   └── content.md
    │   ├── one
    │   │   ├── a
    │   │   │   └── content.md
    │   │   ├── b
    │   │   │   └── content.md
    │   │   ├── c
    │   │   │   └── content.md
    │   │   ├── d
    │   │   │   └── content.md
    │   │   ├── e
    │   │   │   └── content.md
    │   │   ├── f
    │   │   │   └── content.md
    │   │   ├── g
    │   │   │   └── content.md
    │   │   └── content.md
    │   ├── three
    │   │   └── content.md
    │   └── two
    │       └── content.md
    ├── static
    │   ├── css
    │   │   └── reset.css
    │   ├── img
    │   │   └── logo.png
    │   └── favicon.ico
    ├── translations
    └── settings.py

`settings.py` content:

  ::

    from collections import defaultdict
    from webassets import Bundle

    DEFAULT_PAGE = 'one'
    LAYOUTS = defaultdict(lambda: 'page.html', {})
    BUNDLES = {
        'css': Bundle('./css/reset.css', output='./gen/styles.css'),
    }
    ORDERING = {
        '*': ['one', 'two', 'three', 'four'],
        'one/*': 'alphabetically',
    }
    PAGINATION = {
        'one/*': 3,
    }
    PAGE_NAME = 'page%i'

1. The site tree read from `pages` folder:
   
   .. image:: http://dropbucket.ru/id/188

2. Then it gets ordered:

   .. image:: http://dropbucket.ru/id/189
  
3. And paginated:
   
   .. image:: http://dropbucket.ru/id/190

The result directory looks as follows:

  ::

    www
    ├── css
    │   └── reset.css
    ├── four
    │   └── index.html
    ├── img
    │   └── logo.png
    ├── one
    │   ├── a
    │   │   └── index.html
    │   ├── b
    │   │   └── index.html
    │   ├── c
    │   │   └── index.html
    │   ├── d
    │   │   └── index.html
    │   ├── e
    │   │   └── index.html
    │   ├── f
    │   │   └── index.html
    │   ├── g
    │   │   └── index.html
    │   ├── page2
    │   │   └── index.html
    │   ├── page3
    │   │   └── index.html
    │   └── index.html
    ├── three
    │   └── index.html
    ├── two
    │   └── index.html
    ├── favicon.ico
    └── index.html

