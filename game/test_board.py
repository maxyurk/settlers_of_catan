from unittest import TestCase

from game.board import *
from game.pieces import Colony, Road


class TestBoard(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.b = Board()
        cls.player1 = 'player 1'
        cls.player2 = 'player 2'

        location1, location2 = 0, 7
        cls.b.set_location(cls.player1, location1, Colony.Settlement)
        cls.b.set_location(cls.player1, location2, Colony.Settlement)

        cls.b.set_path(cls.player1, (0, 3), Road.Paved)
        cls.b.set_path(cls.player1, (3, 7), Road.Paved)
        cls.b.set_path(cls.player1, (7, 11), Road.Paved)
        cls.b.set_path(cls.player1, (7, 12), Road.Paved)

        cls.b.set_path(cls.player1, (0, 4), Road.Paved)
        cls.b.set_path(cls.player1, (4, 8), Road.Paved)

        location3, location4 = 2, 13
        for location in {2, 6, 10, 15}:
            for harbor, locations_near_harbor in cls.b._locations_by_harbors.items():
                if location in locations_near_harbor:
                    location3 = location
                    cls.harbor = harbor
                    break
        cls.b.set_location(cls.player2, location3, Colony.City)
        cls.b.set_location(cls.player2, location4, Colony.City)

        cls.b.set_path(cls.player2, (8, 13), Road.Paved)
        cls.b.set_path(cls.player2, (13, 9), Road.Paved)
        cls.b.set_path(cls.player2, (9, 5), Road.Paved)
        cls.b.set_path(cls.player2, (5, 2), Road.Paved)
        cls.b.set_path(cls.player2, (2, 6), Road.Paved)
        cls.b.set_path(cls.player2, (6, 10), Road.Paved)
        cls.b.set_path(cls.player2, (10, 15), Road.Paved)
        cls.b.set_path(cls.player2, (15, 20), Road.Paved)
        cls.b.set_path(cls.player2, (20, 25), Road.Paved)
        cls.b.set_path(cls.player2, (25, 19), Road.Paved)
        cls.b.set_path(cls.player2, (19, 14), Road.Paved)
        cls.b.set_path(cls.player2, (14, 10), Road.Paved)

    def test___init__(self):
        self.assertIsNotNone(self.b)
        self.assertEqual(len(self.b._roads_and_colonies.nodes()), 54)
        self.assertEqual(len(self.b._lands), 19)

    def test_get_settleable_locations_by_player(self):
        self.assertListEqual(self.b.get_settleable_locations_by_player(self.player1), [])

    def test_get_settleable_locations_by_player_when_game_begins(self):
        b = Board()
        p1 = 'player1'
        p2 = 'player2'
        self.assertEqual(b.get_settleable_locations_by_player(p1), [i for i in range(54)])
        self.assertEqual(b.get_settleable_locations_by_player(p2), [i for i in range(54)])

        b.set_location(p1, 0, Colony.Settlement)
        self.assertEqual(b.get_settleable_locations_by_player(p1), [i for i in range(54) if i not in {0, 3, 4}])
        self.assertEqual(b.get_settleable_locations_by_player(p2), [i for i in range(54) if i not in {0, 3, 4}])

        b.set_path(p1, (0, 4), Road.Paved)
        b.set_path(p1, (4, 1), Road.Paved)
        b.set_path(p1, (0, 3), Road.Paved)
        b.set_path(p1, (3, 7), Road.Paved)
        b.set_location(p1, 7, Colony.Settlement)
        self.assertEqual(b.get_settleable_locations_by_player(p1), [1])
        self.assertEqual(b.get_settleable_locations_by_player(p2),
                         [i for i in range(54) if i not in {0, 3, 4, 7, 11, 12}])

    def test_get_unpaved_paths_near_player(self):
        paths = self.b.get_unpaved_paths_near_player(self.player1)
        self.assertEqual(len(paths), 5)
        self.assertIn((4, 1), paths)
        self.assertIn((16, 11), paths)
        self.assertIn((12, 8), paths)
        self.assertIn((17, 12), paths)

    def test_get_settled_locations_by_player(self):
        self.assertListEqual(self.b.get_locations_colonised_by_player(self.player1), [0, 7])

    def test_get_surrounding_resources(self):
        self.assertListEqual(self.b.get_surrounding_resources(30),
                             [self.b._lands[9].resource, self.b._lands[10].resource, self.b._lands[14].resource])

    def test_get_colonies_score(self):
        self.assertEqual(self.b.get_colonies_score(self.player1), 2)
        self.assertEqual(self.b.get_colonies_score(self.player2), 4)

    def test_get_longest_road_length_of_player(self):
        self.assertEqual(self.b.get_longest_road_length_of_player(self.player1), 5)
        self.assertEqual(self.b.get_longest_road_length_of_player(self.player2), 12)

    def test_is_player_on_harbor(self):
        self.assertTrue(self.b.is_player_on_harbor(self.player2, self.harbor))
