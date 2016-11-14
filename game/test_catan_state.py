from unittest import TestCase

from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from game.catan_state import CatanState
from game.pieces import Colony, Road


class FakePlayer(AbstractPlayer):
    def __init__(self, identifier):
        super().__init__()
        self.id = identifier

    def choose_move(self, state: AbstractState):
        pass


class TestCatanState(TestCase):

    def setUp(self):
        super().setUp()
        self.players = [FakePlayer(i) for i in range(2)]
        self.state = CatanState(self.players)

    def test_is_final(self):
        self.assertFalse(self.state.is_final())

        for i in range(21, 26):
            self.state._board.set_location(self.players[0], i, Colony.City)

        self.assertTrue(self.state.is_final())

    def test_get_next_moves_given_resources_for_single_road(self):
        # given this board
        self.state._board.set_location(self.players[0], 0, Colony.Settlement)
        self.state._board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state._board.set_path(self.players[0], (3, 7), Road.Paved)

        # without resources, assert there's only the "no move" move
        moves = self.state.get_next_moves()
        self.assertEqual(len(moves), 1)
        move = moves[0]
        self.assertListEqual(move.development_cards_to_be_exposed, [])
        self.assertListEqual(move.paths_to_be_paved, [])
        self.assertListEqual(move.locations_to_be_set_to_settlements, [])
        self.assertListEqual(move.locations_to_be_set_to_cities, [])
        self.assertEqual(move.development_cards_to_be_purchased_count, 0)

        # add resources to pave road
        self.players[0].add_resources_for_road()

        # assert only road paving in logical locations is possible
        moves = self.state.get_next_moves()
        self.assertEqual(len(moves), 4)
        expected_possible_roads = {(0, 4), (7, 11), (7, 12)}
        actual_possible_roads = set()
        for move in moves:
            self.assertListEqual(move.development_cards_to_be_exposed, [])
            self.assertListEqual(move.locations_to_be_set_to_settlements, [])
            self.assertListEqual(move.locations_to_be_set_to_cities, [])
            self.assertEqual(move.development_cards_to_be_purchased_count, 0)
            if len(move.paths_to_be_paved) != 0:  # if not the "empty move"
                self.assertEqual(len(move.paths_to_be_paved), 1)
                actual_possible_roads.add(move.paths_to_be_paved[0])

        self.assertSetEqual(expected_possible_roads, actual_possible_roads)

    def test_make_move(self):
        self.fail()

    def test_unmake_move(self):
        self.fail()

    def test_get_current_player(self):
        self.fail()

    def test_throw_dice(self):
        self.state._board.set_location(self.players[0], 0, Colony.Settlement)
        land_resource = self.state._board._lands[0][0]
        land_number = self.state._board._lands[0][1]

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)

        # this is what happens in throw_dice, except I decided what the number is,
        # instead of "throwing the dice"
        self.state._on_thrown_dice_update_resources(land_number, AbstractPlayer.add_resource)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

    def test_unthrow_dice(self):
        self.state._board.set_location(self.players[0], 0, Colony.Settlement)
        land_resource = self.state._board._lands[0][0]
        land_number = self.state._board._lands[0][1]

        # this is what happens in throw_dice, except I decided what the number is,
        # instead of "throwing the dice"
        self.state._on_thrown_dice_update_resources(land_number, AbstractPlayer.add_resource)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

        self.state.unthrow_dice(land_number)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)

