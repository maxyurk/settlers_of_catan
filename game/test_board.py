from unittest import TestCase

from game.Board import *


class TestBoard(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.b = Board()
        cls.player1 = 'player 1'
        cls.player2 = 'player 2'

        cls.b.settle_location(cls.player1, 0, Colony.Settlement)
        cls.b.pave_road(cls.player1, (0, 3))
        cls.b.pave_road(cls.player1, (3, 7))
        cls.b.pave_road(cls.player1, (7, 11))
        cls.b.pave_road(cls.player1, (7, 12))
        cls.b.pave_road(cls.player1, (0, 4))
        cls.b.pave_road(cls.player1, (4, 8))
        cls.b.settle_location(cls.player2, 8, Colony.Settlement)
        cls.b.pave_road(cls.player2, (8, 13))
        cls.b.pave_road(cls.player2, (13, 9))

    def test___init__(self):
        self.assertIsNotNone(self.b)
        self.assertEqual(len(self.b._roads_and_colonies.nodes()), 54)
        self.assertEqual(len(self.b._lands), 19)

    def test_get_all_settleable_locations(self):
        self.assertEqual(len(self.b.get_all_settleable_locations()), 52)

    def test_get_settleable_locations_by_player(self):
        locations = self.b.get_settleable_locations_by_player(self.player1)

        self.assertEqual(len(locations), 2)
        self.assertIn(7, locations)
        self.assertIn(11, locations)

    def test_get_unpaved_roads_near_player(self):
        paths = self.b.get_unpaved_roads_near_player(self.player1)

        self.assertEqual(len(paths), 4)
        self.assertIn((4, 1), paths)
        self.assertIn((11, 16), paths)
        self.assertIn((12, 8), paths)
        self.assertIn((12, 17), paths)

    def test_get_settled_locations_by_player(self):
        locations = self.b.get_settled_locations_by_player(self.player1)

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], 0)

    def test_get_surrounding_resources(self):
        lands = self.b.get_surrounding_resources(30)

        self.assertListEqual(lands, [
            self.b._lands[9], self.b._lands[10], self.b._lands[14]])


