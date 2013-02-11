# coding: utf-8
import os
import shutil
import tempfile
import unittest

from jinja2 import TemplateSyntaxError
from webassets import Bundle

from carcade.core import get_translations
from carcade.environments import create_assets_env, create_jinja2_env


class WebassetsEnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.build_dir)

    def test(self):
        bundle = Bundle('one.css', 'two.css', output='styles.css')
        assets_env = create_assets_env('./tests/fixtures/bundle', self.build_dir, {})
        bundle.build(env=assets_env)

        self.assertTrue('styles.css' in os.listdir(self.build_dir))


class Jinja2EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.build_dir)

    def test_webassets_integration(self):
        template = '{% assets "css" %}{{ ASSET_URL }}{% endassets %}'
        assets_env = create_assets_env('./tests/fixtures/bundle', self.build_dir, {
            'css': Bundle('one.css', 'two.css', output='styles.css')
        })
        jinja2_env = create_jinja2_env(assets_env=assets_env)
        result = jinja2_env.from_string(template).render()
        self.assertTrue('styles.css' in result)

    def test_translations_integration(self):
        template = '{% trans %}Hey!{% endtrans %}'

        jinja2_env = create_jinja2_env()
        result = jinja2_env.from_string(template).render()
        self.assertEqual('Hey!', result)

        translations = get_translations('tests/fixtures/ru.po')
        jinja2_env = create_jinja2_env(translations=translations)
        result = jinja2_env.from_string(template).render()
        self.assertEqual(u'Привет!', result)
