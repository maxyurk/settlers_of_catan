from unittest import TestCase

from game.Board import *


class TestBoard(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.b = Board()

    def test___init__(self):
        self.assertIsNotNone(self.b)
        self.assertEqual(len(self.b._roads_and_colonies.nodes()), 54)
        self.assertEqual(len(self.b._lands), 19)

    def test_get_all_settleable_locations(self):
        self.assertEqual(len(self.b.get_all_settleable_locations()), 54)

    def test_get_settleable_locations_by_player(self):
        player1 = 'player 1'
        player2 = 'player 2'
        self.b.settle_location(player1, 0, Colony.Settlement)
        self.b.pave_road(player1, (0, 3))
        self.b.pave_road(player1, (3, 7))
        self.b.pave_road(player1, (0, 4))
        self.b.pave_road(player1, (4, 8))
        self.b.settle_location(player2, 4, Colony.Settlement)

        locations = self.b.get_settleable_locations_by_player(player1)

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], 7)
        self.assertEqual((locations[1], Colony.Uncolonised))

    def test_get_unpaved_roads_near_player(self):
        pass

    def test_get_settled_locations_by_player(self):
        pass
