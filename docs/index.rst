Welcome to Carcade's documentation!
===================================

Carcade is the static site generator written in Python. The main features are:

* Jinja2 templates
* Static assets management
* Easy localization
* And, unlike many other static site generators,
  Carcade doesn't make any assumptions about the site structure.

The main idea
-------------
Static site can be considered as a tree with nodes corresponding to the site pages.

Suppose each node has the context -- dictionary containing page data -- and consider the following thoughts:

* to display the main menu on every page of the site, it's enough to have access to
  the contexts of the first-level pages of the tree. Something like:

  ::

    {% for child in ROOT.CHILDREN %}
      <a href="{{ url_for(child.PATH) }}">{{ child.name }}</a>
    {% endfor %}

* to display page containing the list of blog entries, it's enough to have access to the
  contexts of all child nodes of the `/blog/` page:

  ::

    <ul>
      {% for post in CHILDREN %}
        <li>
          <a href="{{ url_for(post.PATH) }}">{{ post.title }}</a>
          <p>{{ post.summary }}</p>
        <li>
      {% endfor %}
    </ul>

* and so on :)

That's the main idea lying behind Carcade: it gives you powerful Jinja2 templates,
where you can refer to the context of any of the tree nodes.

Content
-------

.. toctree::
   :maxdepth: 2

   overview
   example
   settings
   cli
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
