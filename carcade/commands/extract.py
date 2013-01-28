from carcade.i18n import extract_translations
from carcade.environments import create_jinja2_env


def main():
    jinja2_env = create_jinja2_env()
    extract_translations(jinja2_env, 'translations/messages.pot')
