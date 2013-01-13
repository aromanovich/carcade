import unittest

from carcade.core import create_tree


class Test(unittest.TestCase):
    def test(self):
        import os
        print os.getcwd()
        tree = create_tree('./tests/fixture/', 'ru')
        expected_tree_structure = {
            'a': {
                'a/1': {
                    'a/1/hello': {},
                },
                'a/2': {},
            },
            'b': {},
            'c': {},
        }
        self.assert_tree_structure(tree, expected_tree_structure)

    def assert_tree_structure(self, tree, expected_tree_structure):
        self.assertEquals(
            set(subtree.name for subtree in tree.children),
            set(expected_tree_structure.keys()))
        
        for subtree in tree.children:
            self.assert_tree_structure(
                subtree, expected_tree_structure[subtree.name])



