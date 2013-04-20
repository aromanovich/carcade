Command line interface
======================

All the commands except ``init`` must be run inside the project directory.

* ``carcade init``

  Creates new Carcade project.

* ``carcade build [--atomically] [--to ./www]``

  Builds the site.

  If you want to put this command to cron jobs at the production server,
  consider using ``--atomically`` key -- in that case Carcade will update
  the target directory as atomically as possible. :)

* ``carcade runserver [--host localhost] [--port 8000]``

  Fires up the development server that will host `./www` directory, monitor
  the changes and regenerate the site automatically.

* ``carcade extract-messages [--to ./translations/messages.pot]``
 
  Extracts localizable strings from the templates. 
