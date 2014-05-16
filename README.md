character giveaway
==================

This site runs easily on dokku (and heroku?). Use `runserver.py` for local development.

You need a postgres database and email account. Copy `config.py.dist` to `config.py`
and configure. When pushing to dokku or heroku you'll need to force add your
`config.py` in order to push it because it's in `.gitignore`.

This is probably useless if you don't partake in <http://wotmud.org>.
