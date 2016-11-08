from unittest import TestCase

from game.Board import Board


class TestBoard(TestCase):

    def setUp(self):
        super().setUp()
        self.b = Board()
        print('hello')

    def test___init__(self):
        self.assertIsNotNone(self.b)
        self.assertEqual(len(self.b._roads_and_settlements.nodes()), 54)
        self.assertEqual(len(self.b._lands), 20)

    def test_get_all_settleable_locations(self):
        pass

    def test_get_settleable_locations_by_player(self):
        pass

    def test_get_unpaved_roads_near_player(self):
        pass

    def test_get_settled_locations_by_player(self):
        pass
