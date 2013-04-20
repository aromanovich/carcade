import unittest

from carcade.core import create_tree, paginate_tree, sort_tree


class Test(unittest.TestCase):
    def assert_tree_structure(self, tree, expected_tree_structure):
        self.assertEquals(
            set(subtree.name for subtree in tree.children),
            set(expected_tree_structure.keys()))
        
        for subtree in tree.children:
            self.assert_tree_structure(
                subtree, expected_tree_structure[subtree.name])

    def test_creation(self):
        tree = create_tree('./tests/fixtures/fixture/', 'ROOT')
        expected_tree_structure = {
            'a': {
                '1': {
                    'hello': {},
                },
                '2': {},
            },
            'b': {},
            'c': {},
        }
        self.assert_tree_structure(tree, expected_tree_structure)

    def test_pagination(self):
        tree = create_tree('./tests/fixtures/fixture2/', 'ROOT')
        expected_tree_structure = {
            'blog': {
                'a': {},
                'b': {},
                'c': {},
                'd': {},
                'e': {},
                'f': {},
                'g': {},
            },
        }
        self.assert_tree_structure(tree, expected_tree_structure)

        tree = sort_tree(tree, {'blog': 'alphabetically'})
        tree = paginate_tree(tree, {'blog': 2})
        expected_tree_structure = {
            'blog': {
                'page1': {
                    'a': {},
                    'b': {},
                },
                'page2': {
                    'c': {},
                    'd': {},
                },
                'page3': {
                    'e': {},
                    'f': {},
                },
                'page4': {
                    'g': {},
                },
            },
        }
        self.assert_tree_structure(tree, expected_tree_structure)
