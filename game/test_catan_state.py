from itertools import combinations_with_replacement, combinations
from math import ceil
from unittest import TestCase

from algorithms.abstract_state import AbstractState
from game.board import Harbor
from game.catan_moves import CatanMove, RandomMove
from game.catan_state import CatanState
from game.development_cards import DevelopmentCard
from game.pieces import Colony, Road
from game.resource import Resource
from players.abstract_player import AbstractPlayer


class FakePlayer(AbstractPlayer):
    def __init__(self, identifier):
        super().__init__()
        self.id = identifier

    def choose_move(self, state: AbstractState):
        raise NotImplementedError()

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
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 39, Colony.Settlement)
        self.state.board.set_location(self.players[1], 40, Colony.Settlement)
        self.state.board.set_path(self.players[1], (39, 44), Road.Paved)
        self.state.board.set_path(self.players[1], (40, 44), Road.Paved)
        self.state.turns_count = 4

        # without resources, assert there's only the "no move" move
        moves = self.state.get_next_moves()
        self.assertEqual(len(moves), 1)
        move = moves[0]
        self.assertIsNone(move.development_card_to_be_exposed)
        self.assertDictEqual(move.paths_to_be_paved, {})
        self.assertListEqual(move.locations_to_be_set_to_settlements, [])
        self.assertListEqual(move.locations_to_be_set_to_cities, [])
        self.assertEqual(move.development_cards_to_be_purchased_count, 0)

        # add resources to pave road
        self.players[0].add_resources_and_piece_for_road()

        # assert only road paving in logical locations is possible
        moves = self.state.get_next_moves()
        self.assertEqual(len(moves), 4)
        expected_possible_roads = {(4, 0), (11, 7), (12, 7)}
        actual_possible_roads = set()
        for move in moves:
            self.assertIsNone(move.development_card_to_be_exposed)
            self.assertListEqual(move.locations_to_be_set_to_settlements, [])
            self.assertListEqual(move.locations_to_be_set_to_cities, [])
            self.assertEqual(move.development_cards_to_be_purchased_count, 0)
            if len(move.paths_to_be_paved) != 0:  # if not the "empty move"
                self.assertEqual(len(move.paths_to_be_paved), 1)
                actual_possible_roads.add(next(iter(move.paths_to_be_paved)))

        self.assertSetEqual(expected_possible_roads, actual_possible_roads)

    def test_get_next_moves_returns_only_moves_that_change_robber_placement_when_dice_roll_7(self):
        # given this board
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 50, Colony.Settlement)
        self.state.board.set_location(self.players[1], 42, Colony.Settlement)
        self.state.board.set_path(self.players[1], (50, 46), Road.Paved)
        self.state.board.set_path(self.players[1], (46, 42), Road.Paved)
        self.state.turns_count = 4

        # assert initial robber placement is on the desert land
        self.assertEqual(self.state.board.get_robber_land().resource, None)

        # roll 7
        roll_7 = RandomMove(7, self.state.probabilities_by_dice_values[7], self.state)
        self.state.make_random_move(roll_7)

        # assert all next moves move the robber
        moves = self.state.get_next_moves()
        for move in moves:
            self.assertNotEqual(move.robber_placement_land, self.state.board.get_robber_land())
            self.assertNotEqual(move.robber_placement_land, None)

        # make some move
        self.state.make_move(moves[0])

        # roll 7 again
        self.state.make_random_move(roll_7)

        # assert all next moves move the robber again
        for move in self.state.get_next_moves():
            self.assertNotEqual(move.robber_placement_land, self.state.board.get_robber_land())
            self.assertNotEqual(move.robber_placement_land, None)

    def test_largest_army_is_updated(self):
        for i in range(6):
            if i % 2 == 1:
                # on player2 turn, don't do anything
                self.state.make_move(CatanMove(self.state.board.get_robber_land()))
                continue

            # assert no-one has largest army yet
            player, threshold = self.state._get_largest_army_player_and_size()
            self.assertEqual(player, None)
            self.assertEqual(threshold, 2)

            # add knight dev-card
            self.players[0].add_unexposed_development_card(DevelopmentCard.Knight)

            # expose the knight card
            move = CatanMove(self.state.board.get_robber_land())
            move.development_card_to_be_exposed = DevelopmentCard.Knight
            self.state.make_move(move)

        player, threshold = self.state._get_largest_army_player_and_size()
        self.assertEqual(player, self.players[0])
        self.assertEqual(threshold, 3)

    def test_on_knight_card_exposure_players_drop_cards(self):
        robber_placement = self.state.board.get_robber_land()
        self.players[0].add_unexposed_development_card(DevelopmentCard.Knight)

        for move in self.state.get_next_moves():
            if move.development_card_to_be_exposed == DevelopmentCard.Knight:
                self.assertNotEqual(robber_placement, move.robber_placement_land)
            else:
                self.assertEqual(robber_placement, move.robber_placement_land)

    def test_on_road_building_exposure_player_paves_two_roads(self):
        # given this board
        player = self.players[0]
        self.state.board.set_location(player, 0, Colony.Settlement)
        self.state.board.set_location(player, 7, Colony.Settlement)
        self.state.board.set_path(player, (3, 0), Road.Paved)
        self.state.board.set_path(player, (3, 7), Road.Paved)
        # and player has road-building card
        player.add_unexposed_development_card(DevelopmentCard.RoadBuilding)

        # get all moves
        moves = self.state.get_next_moves()

        # remove the empty move
        moves = list(filter(CatanMove.is_doing_anything, moves))

        # assert moves expose the development-card, and pave two roads
        do_moves_expose_card = (m.development_card_to_be_exposed == DevelopmentCard.RoadBuilding for m in moves)
        self.assertTrue(all(do_moves_expose_card))

        do_moves_pave_two_roads = (len(m.paths_to_be_paved) == 2 for m in moves)
        self.assertTrue(all(do_moves_pave_two_roads))

    def test_on_monopoly_exposed_players_give_resource(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 39, Colony.Settlement)
        self.state.board.set_location(self.players[1], 40, Colony.Settlement)
        self.state.board.set_path(self.players[1], (39, 44), Road.Paved)
        self.state.board.set_path(self.players[1], (40, 44), Road.Paved)
        self.state.turns_count = 4

        # given player 0 has monopoly dev-card, and player 1 has 1 of each resource
        self.players[0].add_unexposed_development_card(DevelopmentCard.Monopoly)
        for resource in Resource:
            self.players[1].add_resource(resource)

        # get all moves
        moves = self.state.get_next_moves()

        # assert correct amount of moves and resources
        self.assertEqual(len(moves), len(Resource) + 1)
        self.assertEqual(self.players[0].get_resource_count(Resource(0)), 0)
        self.assertEqual(self.players[1].get_resource_count(Resource(0)), 1)

        # apply a move that uses monopoly card
        self.state.make_move(moves[1])
        self.state.make_random_move(RandomMove(7, 0.1, self.state))

        # assert cards were taken
        self.assertEqual(self.players[0].get_resource_count(Resource(0)), 1)
        self.assertEqual(self.players[1].get_resource_count(Resource(0)), 0)


        # remove the empty move


    def test_make_move(self):
        self.assertListEqual(self.state.board.get_locations_colonised_by_player(self.players[0]), [])

        self.players[0].add_resources_and_piece_for_settlement()
        move = CatanMove(self.state.board.get_robber_land())
        move.locations_to_be_set_to_settlements.append(0)
        self.state.make_move(move)

        self.assertListEqual(self.state.board.get_locations_colonised_by_player(self.players[0]), [0])

    def test_unmake_move(self):
        self.players[0].add_resources_and_piece_for_settlement()
        move = CatanMove(self.state.board.get_robber_land())
        move.locations_to_be_set_to_settlements.append(0)
        self.state.make_move(move)

        self.assertListEqual(self.state.board.get_locations_colonised_by_player(self.players[0]), [0])

        self.state.unmake_move(move)

    def test_get_current_player(self):
        self.assertEqual(self.state.get_current_player(), self.players[0])
        self.state.make_move(CatanMove(self.state.board.get_robber_land()))
        self.state.make_random_move()
        self.assertEqual(self.state.get_current_player(), self.players[1])
        self.state.make_move(CatanMove(self.state.board.get_robber_land()))
        self.state.make_random_move()
        self.assertEqual(self.state.get_current_player(), self.players[0])

    def test_throw_dice(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 1, Colony.Settlement)
        self.state.board.set_path(self.players[0], (0, 4), Road.Paved)
        self.state.board.set_path(self.players[0], (4, 1), Road.Paved)
        self.state.board.set_location(self.players[1], 50, Colony.Settlement)
        self.state.board.set_location(self.players[1], 42, Colony.Settlement)
        self.state.board.set_path(self.players[1], (50, 46), Road.Paved)
        self.state.board.set_path(self.players[1], (46, 42), Road.Paved)
        self.state.turns_count = 4

        land_resource = self.state.board._lands[0].resource
        dice_value = self.state.board._lands[0].dice_value

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)
        roll_dice = RandomMove(dice_value, self.state.probabilities_by_dice_values[dice_value], self.state)
        self.state.make_random_move(roll_dice)
        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

    def test_unthrow_dice(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 29, Colony.Settlement)
        self.state.board.set_path(self.players[0], (0, 4), Road.Paved)
        self.state.board.set_path(self.players[0], (29, 35), Road.Paved)
        self.state.board.set_location(self.players[1], 50, Colony.Settlement)
        self.state.board.set_location(self.players[1], 42, Colony.Settlement)
        self.state.board.set_path(self.players[1], (50, 46), Road.Paved)
        self.state.board.set_path(self.players[1], (46, 42), Road.Paved)
        self.state.turns_count = 4

        land_resource = self.state.board._lands[0].resource
        dice_value = self.state.board._lands[0].dice_value

        roll_dice = RandomMove(dice_value, self.state.probabilities_by_dice_values[dice_value], self.state)
        self.state.make_random_move(roll_dice)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 1)

        self.state.unmake_random_move(roll_dice)

        self.assertEqual(self.players[0].get_resource_count(land_resource), 0)

    def test_get_all_possible_development_cards_purchase_options(self):
        purchase_count = 2
        options = self.state._get_all_possible_development_cards_purchase_options(purchase_count)

        # assert the number of options is (26 choose 2) (because there are 26 unexposed cards)
        number_of_cards_combinations = sum(1 for _ in combinations_with_replacement(DevelopmentCard, purchase_count))
        self.assertEqual(len(options), number_of_cards_combinations)

        # assert all options are different
        for option1, option2 in combinations(options, 2):
            self.assertNotEqual(option1, option2)
            self.assertNotEqual(option1.purchased_cards_counters, option2.purchased_cards_counters)

        # assert all probabilities are valid probabilities, and there are no moves where probability = 0
        for option in options:
            self.assertLess(option.probability, 1)
            self.assertGreater(option.probability, 0)

        # this assertion is just to make sure I'm testing the probability of the right options
        two_knights_counters = {card: purchase_count if card is DevelopmentCard.Knight else 0
                                for card in DevelopmentCard}
        assert options[0].purchased_cards_counters == two_knights_counters

        # assert the probability is right, given no knight was exposed (there are 15 knight in total)
        two_knight_cards_expected_probability = (15 / 26) * (14 / 25)
        two_knight_cards_actual_probability = options[0].probability
        self.assertAlmostEqual(two_knight_cards_expected_probability, two_knight_cards_actual_probability)

    def test_probability_calculation_given_card_used(self):
        # given this board
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 39, Colony.Settlement)
        self.state.board.set_location(self.players[1], 40, Colony.Settlement)
        self.state.board.set_path(self.players[1], (39, 44), Road.Paved)
        self.state.board.set_path(self.players[1], (40, 44), Road.Paved)
        self.state.turns_count = 4

        # buy two knight cards
        self.state.make_move(CatanMove(self.state.board.get_robber_land()))
        purchase_count = 2
        two_knight_cards_expected_probability = (15 / 26) * (14 / 25)
        two_knights_counters = {card: purchase_count if card is DevelopmentCard.Knight else 0
                                for card in DevelopmentCard}
        self.state.make_random_move(
            RandomMove(2, two_knight_cards_expected_probability * self.state.probabilities_by_dice_values[2],
                       self.state, two_knights_counters))

        # make empty move
        self.state.make_move(CatanMove(self.state.board.get_robber_land()))
        self.state.make_random_move(RandomMove(2, self.state.probabilities_by_dice_values[2], self.state))

        # expose one knight
        move = CatanMove(self.state.board._lands[0])
        move.development_card_to_be_exposed = DevelopmentCard.Knight
        self.state.make_move(move)
        self.state.make_random_move(RandomMove(2, self.state.probabilities_by_dice_values[2], self.state))

        # get all purchase options of two cards
        options = self.state._get_all_possible_development_cards_purchase_options(purchase_count)

        # assert the number of options is (25 choose 2) (because there are 25 unexposed cards)
        number_of_cards_combinations = sum(1 for _ in combinations_with_replacement(DevelopmentCard, purchase_count))
        self.assertEqual(len(options), number_of_cards_combinations)

        # assert all options are different
        for option1, option2 in combinations(options, 2):
            self.assertNotEqual(option1, option2)
            self.assertNotEqual(option1.purchased_cards_counters, option2.purchased_cards_counters)

        # assert all probabilities are valid probabilities, and there are no moves where probability = 0
        for option in options:
            self.assertLess(option.probability, 1)
            self.assertGreater(option.probability, 0)

        # this assertion is just to make sure I'm testing the probability of the right options
        assert options[0].purchased_cards_counters == two_knights_counters

        # assert the probability is right, given one knight was exposed
        two_knight_cards_expected_probability = (14 / 25) * (13 / 24)
        two_knight_cards_actual_probability = options[0].probability
        self.assertAlmostEqual(two_knight_cards_expected_probability, two_knight_cards_actual_probability)

    def test_get_all_possible_trade_moves_empty_move_no_resources(self):
        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]

    def test_get_all_possible_trade_moves_empty_move_not_enough_resources(self):
        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        for _ in range(3):
            for resource in Resource:
                self.players[0].add_resource(resource)
            moves = self.state._get_all_possible_trade_moves(moves)
            assert moves == [empty_move]

    def test_get_all_possible_trade_moves_single_trade(self):
        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        self.players[0].add_resource(Resource.Lumber, 4)
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves[0] == empty_move
        assert len(moves[1].resources_exchanges) == 1
        assert len(moves[2].resources_exchanges) == 1
        assert len(moves[3].resources_exchanges) == 1
        assert len(moves[4].resources_exchanges) == 1
        assert len(moves) == 5

    def test_get_all_possible_trade_moves_different_ratio_generic(self):
        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        self.players[0].add_resource(Resource.Lumber, 2)
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        self.players[0].add_resource(Resource.Lumber, 1)
        self.state.board._locations_by_harbors[Harbor.HarborGeneric].append(0)
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves[0] == empty_move
        assert len(moves[1].resources_exchanges) == 1
        assert len(moves[2].resources_exchanges) == 1
        assert len(moves[3].resources_exchanges) == 1
        assert len(moves[4].resources_exchanges) == 1
        assert len(moves) == 5

    def test_get_all_possible_trade_moves_different_ratio_non_generic(self):
        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        self.players[0].add_resource(Resource.Lumber, 1)
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves == [empty_move]
        self.players[0].add_resource(Resource.Lumber, 1)
        self.state.board._locations_by_harbors[Harbor.HarborLumber].append(0)
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        moves = self.state._get_all_possible_trade_moves(moves)
        assert moves[0] == empty_move
        assert len(moves[1].resources_exchanges) == 1
        assert len(moves[2].resources_exchanges) == 1
        assert len(moves[3].resources_exchanges) == 1
        assert len(moves[4].resources_exchanges) == 1
        assert len(moves) == 5

    def test_get_all_possible_development_cards_exposure_moves(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 39, Colony.Settlement)
        self.state.board.set_location(self.players[1], 40, Colony.Settlement)
        self.state.board.set_path(self.players[1], (39, 44), Road.Paved)
        self.state.board.set_path(self.players[1], (40, 44), Road.Paved)
        self.state.turns_count = 4

        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_development_cards_exposure_moves(moves)
        self.assertEqual(moves, [empty_move])
        self.players[0].add_unexposed_development_card(DevelopmentCard.RoadBuilding)
        self.players[0].add_unexposed_development_card(DevelopmentCard.YearOfPlenty)
        self.players[0].add_unexposed_development_card(DevelopmentCard.Monopoly)
        self.players[0].add_unexposed_development_card(DevelopmentCard.Knight)
        self.players[0].add_unexposed_development_card(DevelopmentCard.VictoryPoint)
        moves = self.state._get_all_possible_development_cards_exposure_moves(moves)
        self.assertEqual(moves[0], empty_move)
        all_dev_cards = [move.development_card_to_be_exposed for move in moves]
        for dev_card_type in DevelopmentCard:
            assert dev_card_type in all_dev_cards
        self.assertEqual(len(moves), 41)
        knight_dev_applied_moves = [move for move in moves if move.development_card_to_be_exposed == DevelopmentCard.Knight]
        self.assertEqual(len(knight_dev_applied_moves), 18)
        y_o_p_dev_applied_moves = [move for move in moves if move.development_card_to_be_exposed == DevelopmentCard.YearOfPlenty]
        self.assertEqual(len(y_o_p_dev_applied_moves), 15)
        monopoly_dev_applied_moves = [move for move in moves if move.development_card_to_be_exposed == DevelopmentCard.Monopoly]
        self.assertEqual(len(monopoly_dev_applied_moves), 5)

    def test_get_all_possible_path_moves(self):
        self.state.board.set_location(self.players[0], 0, Colony.Settlement)
        self.state.board.set_location(self.players[0], 7, Colony.Settlement)
        self.state.board.set_path(self.players[0], (3, 0), Road.Paved)
        self.state.board.set_path(self.players[0], (3, 7), Road.Paved)
        self.state.board.set_location(self.players[1], 39, Colony.Settlement)
        self.state.board.set_location(self.players[1], 40, Colony.Settlement)
        self.state.board.set_path(self.players[1], (39, 44), Road.Paved)
        self.state.board.set_path(self.players[1], (40, 44), Road.Paved)
        self.state.turns_count = 4

        empty_move = CatanMove(self.state.board.get_robber_land())
        moves = [empty_move]
        moves = self.state._get_all_possible_paths_moves(moves)
        self.assertEqual(moves, [empty_move])
        self.players[0].add_resource(Resource.Lumber)
        self.players[0].add_resource(Resource.Brick)

        # First player
        moves = [empty_move]
        moves = self.state._get_all_possible_paths_moves(moves)
        self.assertEqual(len(moves), 4)

        # move to next player
        self.state.make_move(empty_move)
        self.state.make_random_move(RandomMove(2, 0.1, self.state))

        self.players[1].add_resource(Resource.Lumber)
        self.players[1].add_resource(Resource.Brick)

        # Second player
        moves = [empty_move]
        moves = self.state._get_all_possible_paths_moves(moves)
        self.assertEqual(len(moves), 6)
