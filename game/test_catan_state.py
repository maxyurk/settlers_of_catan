from unittest import TestCase
from math import ceil
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from game.board import Resource
from game.catan_state import CatanState, CatanMove
from game.pieces import Colony, Road


class FakePlayer(AbstractPlayer):
    def __init__(self, identifier):
        super().__init__()
        self.id = identifier

    def choose_move(self, state: AbstractState):
        pass

    def choose_resources_to_drop(self):
        sum_of_resources = sum(self.resources.values())
        if sum_of_resources < 8:
            return {}

        drop_count = ceil(len(sum_of_resources) / 2)
        resources_to_drop = {resource: 0 for resource in Resource}
        for resource, resource_count in self.resources.items():
            if resource_count >= drop_count:
                resources_to_drop[resource] = drop_count
                return resources_to_drop
            else:
                resources_to_drop[resource] = resource_count
                drop_count -= resource_count

        return resources_to_drop


class TestCatanState(TestCase):

    def setUp(self):
        super().setUp()
        self.players = [FakePlayer(i) for i in range(2)]
        self.state = CatanState(self.players)

    def test_is_final(self):
        self.assertFalse(self.state.is_final())

        for i in range(21, 26):
            self.state.board.set_location(self.players[0], i, Colony.City)

        self.assertTrue(self.state.is_final())

    def test_get_next_moves_given_resources_for_single_road(self):
        # given this board
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)

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

    def test_get_next_moves_returns_only_moves_that_change_robber_placement_when_dice_roll_7(self):
        # given this board
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 50, Colony.Settlement)
        self.state.board.set_path(self.players[1], (50, 46), Road.Paved)
        self.state.board.set_path(self.players[1], (46, 42), Road.Paved)

        # assert initial robber placement is on the desert land
        self.assertEqual(self.state.board.get_robber_land().resource, None)

        # roll 7
        self.state.throw_dice(rolled_dice_number=7)

        # assert all next moves move the robber
        moves = self.state.get_next_moves()
        for move in moves:
            self.assertNotEqual(move.robber_placement_land, self.state.board.get_robber_land())
            self.assertNotEqual(move.robber_placement_land, None)

        # make some move
        self.state.make_move(moves[0])

        # roll 7 again
        self.state.throw_dice(rolled_dice_number=7)

        # assert all next moves move the robber again
        for move in self.state.get_next_moves():
            self.assertNotEqual(move.robber_placement_land, self.state.board.get_robber_land())
            self.assertNotEqual(move.robber_placement_land, None)

    def test_make_move(self):
        self.assertListEqual(self.state.board.get_settled_locations_by_player(self.players[0]), [])

        self.players[0].add_resources_for_settlement()
        move = CatanMove()
        move.locations_to_be_set_to_settlements.append(0)
        self.state.make_move(move)

        self.assertListEqual(self.state.board.get_settled_locations_by_player(self.players[0]), [0])

    def test_unmake_move(self):
        self.players[0].add_resources_for_settlement()
        move = CatanMove()
        move.locations_to_be_set_to_settlements.append(0)
        self.state.make_move(move)

        self.assertListEqual(self.state.board.get_settled_locations_by_player(self.players[0]), [0])

        self.state.unmake_move(move)

    def test_get_current_player(self):
        self.assertEqual(self.state.get_current_player(), self.players[0])
        self.state.make_move(CatanMove())
        self.assertEqual(self.state.get_current_player(), self.players[1])
        self.state.make_move(CatanMove())
        self.assertEqual(self.state.get_current_player(), self.players[0])

    def test_throw_dice(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        land_resource = self.state.board._lands[0][0]
        land_number = self.state.board._lands[0][1]

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)
        move = self.state.throw_dice(land_number)
        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

    def test_unthrow_dice(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        land_resource = self.state.board._lands[0][0]
        land_number = self.state.board._lands[0][1]

        move = self.state.throw_dice(land_number)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

        self.state.unthrow_dice(move)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)

