import copy
from collections import defaultdict
from collections import namedtuple
from itertools import combinations_with_replacement
from typing import List, Tuple, Dict, Union

import numpy as np

from algorithms.abstract_state import AbstractState
from game.board import Board, Harbor, Location, Path
from game.catan_moves import CatanMove, RandomMove
from game.development_cards import DevelopmentCard
from game.pieces import Colony, Road
from game.resource import Resource, LastResourceIndex, FirsResourceIndex, ResourceAmounts
from players.abstract_player import AbstractPlayer

ResourceExchange = namedtuple('ResourceExchange', ['source_resource', 'target_resource', 'count'])
PurchaseOption = namedtuple('PurchaseOption', ['purchased_cards_counters', 'probability'])
KnightCardsCount = int


class CatanState(AbstractState):
    def __init__(self, players: List[AbstractPlayer], seed=None):
        assert seed is None or (isinstance(seed, int) and seed > 0)

        random_state = np.random.RandomState(seed)
        self._random_choice = random_state.choice

        self.players = players
        self.board = Board(seed)

        self.turns_count = 0
        self._current_player_index = 0
        self.current_dice_number = 0

        self._dev_cards = [DevelopmentCard.Knight] * 15 + \
                          [DevelopmentCard.VictoryPoint] * 5 + \
                          [DevelopmentCard.RoadBuilding,
                           DevelopmentCard.Monopoly,
                           DevelopmentCard.YearOfPlenty] * 2
        random_state.shuffle(self._dev_cards)

        # we must preserve these in the state, since it's possible a
        # player has one of the special cards, while some-one has the
        # same amount of knights-cards used/longest road length
        # i.e when player 1 paved 5 roads, and player too as-well,
        # but only after player 1.
        self._player_with_largest_army = []
        self._player_with_longest_road = []

        self.probabilities_by_dice_values = {}
        for i, p in zip(range(2, 7), range(1, 6)):
            self.probabilities_by_dice_values[i] = p / 36.0
            self.probabilities_by_dice_values[14 - i] = p / 36.0
        self.probabilities_by_dice_values[7] = 6 / 36.0

        self._unexposed_dev_cards_counters = {card: DevelopmentCard.get_occurrences_in_deck_count(card)
                                              for card in DevelopmentCard}
        self._purchased_development_cards_in_current_turn_amount = 0

    def is_final(self):
        """
        check if the current state in the game is final or not
        Returns:
            bool: indicating whether the current state is a final one
        """
        players_points_count = self.get_scores_by_player()

        highest_score = max(players_points_count.values())
        return highest_score >= 10

    def get_scores_by_player(self):
        players_points_count = {player: self.board.get_colonies_score(player)
                                for player in self.players}
        player, _ = self._get_largest_army_player_and_size()
        if player is not None:
            players_points_count[player] += 2
        player, _ = self._get_longest_road_player_and_length()
        if player is not None:
            players_points_count[player] += 2
        for player in self.players:
            players_points_count[player] += player.get_victory_point_development_cards_count()
        return players_points_count

    def get_next_moves(self):
        """computes the next moves available from the current state
        Returns:
            List of AbstractMove: a list of the next moves
        """
        if self.is_initialisation_phase():
            return self._get_initialisation_moves()

        if self.current_dice_number != 7:
            empty_move = CatanMove(self.board.get_robber_land())
            moves = [empty_move]
        else:
            moves = [CatanMove(land) for land in self.board.get_lands_to_place_robber_on()]
        moves = self._get_all_possible_development_cards_exposure_moves(moves)
        # _get_all_possible_trade_moves is assuming it's after dev_cards moves and nothing else
        moves = self._get_all_possible_trade_moves(moves)
        moves = self._get_all_possible_paths_moves(moves)
        moves = self._get_all_possible_settlements_moves(moves)
        moves = self._get_all_possible_cities_moves(moves)
        moves = self._get_all_possible_development_cards_purchase_count_moves(moves)
        return moves

    def make_move(self, move: CatanMove):
        """
        apply move
        :param move: move to apply
        :return: None
        """
        self.turns_count += 1
        self._pretend_to_make_a_move(move)

        self._update_longest_road(move)
        self._update_largest_army(move)

        self._purchased_development_cards_in_current_turn_amount = move.development_cards_to_be_purchased_count

    def unmake_move(self, move: CatanMove):
        """
        revert move
        :param move: move to revert
        :return: None
        """
        self._purchased_development_cards_in_current_turn_amount = 0

        self._revert_update_longest_road(move)
        self._revert_update_largest_army(move)

        self._unpretend_to_make_a_move(move)
        self.turns_count -= 1

    def get_next_random_moves(self) -> List[RandomMove]:
        if self.is_initialisation_phase():
            return [RandomMove(2, 1.0, self)]
        random_moves = []
        for dice_value, dice_probability in self.probabilities_by_dice_values.items():
            for purchase_option, purchase_probability in self._get_all_possible_development_cards_purchase_options(
                    self._purchased_development_cards_in_current_turn_amount):
                random_moves.append(
                    RandomMove(dice_value, dice_probability * purchase_probability, self, purchase_option))
        return random_moves

    def make_random_move(self, random_move: RandomMove = None):
        if random_move is None:
            rolled_dice_value = self._random_choice(a=list(self.probabilities_by_dice_values.keys()),
                                                    p=list(self.probabilities_by_dice_values.values()))
            purchased_development_cards = defaultdict(int)
            for _ in range(self._purchased_development_cards_in_current_turn_amount):
                card = self.pop_development_card()
                purchased_development_cards[card] += 1

            random_move = RandomMove(rolled_dice=rolled_dice_value,
                                     probability=self.probabilities_by_dice_values[rolled_dice_value],
                                     state=self,
                                     development_card_purchases=purchased_development_cards)
        random_move.apply()
        self._purchased_development_cards_in_current_turn_amount = 0
        self._current_player_index = (self._current_player_index + 1) % len(self.players)

    def unmake_random_move(self, random_move: RandomMove):
        self._current_player_index = (self._current_player_index - 1) % len(self.players)
        random_move.revert()

    def get_current_player(self):
        """returns the player that should play next"""
        return self.players[self._current_player_index]

    def pop_development_card(self) -> DevelopmentCard:
        return self._dev_cards.pop()

    def is_initialisation_phase(self) -> bool:
        return self.turns_count < len(self.players) * 2

    def _update_longest_road(self, move: CatanMove):
        if len(move.paths_to_be_paved) == 0:
            return

        player_with_longest_road, length_threshold = self._get_longest_road_player_and_length()
        longest_road_length = self.board.get_longest_road_length_of_player(self.get_current_player())

        if longest_road_length > length_threshold:
            self._player_with_longest_road.append((self.get_current_player(), longest_road_length))
            move.did_get_longest_road_card = True

    def _revert_update_longest_road(self, move: CatanMove):
        if move.did_get_longest_road_card:
            self._player_with_longest_road.pop()

    def _update_largest_army(self, move: CatanMove):
        if move.development_card_to_be_exposed != DevelopmentCard.Knight:
            return

        player_with_largest_army, size_threshold = self._get_largest_army_player_and_size()
        army_size = self.get_current_player().get_exposed_knights_count()

        if army_size > size_threshold:
            self._player_with_largest_army.append((self.get_current_player(), army_size))
            move.did_get_largest_army_card = True

    def _revert_update_largest_army(self, move: CatanMove):
        if move.did_get_largest_army_card:
            self._player_with_largest_army.pop()

    def _get_longest_road_player_and_length(self) -> Tuple[None, int]:
        """
        get player with longest road, and longest road length.
        if No one crossed the 5 roads threshold yet(which means the stack is empty),
        return (None, 4) because that's the threshold to cross
        else, return the last player to cross the threshold
        :return: tuple of (player with longest road, longest road length)
        """
        if not self._player_with_longest_road:
            return None, 4
        return self._player_with_longest_road[-1]

    def _get_largest_army_player_and_size(self) -> Tuple[Union[AbstractPlayer, None], KnightCardsCount]:
        """
        get player with largest army, and largest army size.
        if No one crossed the 2 knights threshold yet(which means the stack is empty),
        return (None, 2) because there's no player yet, and that's the threshold to cross
        else, return the last player to cross the threshold, and the threshold
        :return: tuple of (player with longest road, longest road length)
        """
        if not self._player_with_largest_army:
            return None, 2
        return self._player_with_largest_army[-1]

    def _calc_curr_player_trade_ratio(self, source_resource: Resource):
        """
        return 2, 3 or 4 based on the current players harbors status
        :param source_resource: the resource the player will give
        :return: 2, 3 or 4 - the number of resource units the player will give for a single card
        """
        curr_player = self.get_current_player()
        if self.board.is_player_on_harbor(curr_player, Harbor(source_resource.value)):
            return 2
        if self.board.is_player_on_harbor(curr_player, Harbor.HarborGeneric):
            return 3
        return 4

    def _get_all_possible_trade_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        """
        NOTICE: assuming it's after dev_cards moves and nothing else
        :param moves: moves so far
        :return: moves with trades
        """
        player = self.get_current_player()
        new_moves = []

        no_dev_card_side_effect_trades = []
        for source_resource in Resource:

            max_num_of_trades = (int(player.get_resource_count(source_resource) /
                                     self._calc_curr_player_trade_ratio(source_resource)))
            for i in range(1, max_num_of_trades + 1):
                no_dev_card_side_effect_trades += self._trade_options_with_i_trades_and_min_resource_index(i,
                                                                                                           source_resource,
                                                                                                           FirsResourceIndex)

        for move in moves:
            # assuming it's after dev_cards moves and nothing else (bad programming but better performance)
            if (move.development_card_to_be_exposed == DevelopmentCard.YearOfPlenty or
                    move.development_card_to_be_exposed == DevelopmentCard.Monopoly):
                self._pretend_to_make_a_move(move)
                for source_resource in Resource:
                    max_num_of_trades = int(player.get_resource_count(source_resource) /
                                            self._calc_curr_player_trade_ratio(source_resource))
                    for i in range(1, max_num_of_trades + 1):
                        for trades in self._trade_options_with_i_trades_and_min_resource_index(i, source_resource,
                                                                                               FirsResourceIndex):
                            new_move = copy.deepcopy(move)
                            new_move.resources_exchanges = trades
                            new_moves.append(new_move)
                self._unpretend_to_make_a_move(move)
            else:
                for trades in no_dev_card_side_effect_trades:
                    new_move = copy.deepcopy(move)
                    new_move.resources_exchanges = trades
                    new_moves.append(new_move)

        return moves + new_moves

    def _trade_options_with_i_trades_and_min_resource_index(self, i, source_resource, min_resource_index) \
            -> List[List[ResourceExchange]]:
        """
        Using with i == 0 has no meaning
        Returns all possible trade combinations when making i trades
        returns type is List[List[ResourceExchange]] : List of Lists of ResourceExchanges
        all the counters in each list of ResourceExchanges sum to i.
        :param i: exact number of trades (the list could have a single 'ResourceExchange' obj with count == i)
        :param source_resource: the resource that returns to the cards stack
        :param min_resource_index: the index of the minimal resource allowed to be traded (taken from the cards stack)(initial value is 1)
        :return: Returns all possible trade combinations when making i trades
                 Returns type is List[List[ResourceExchange]] : List of Lists of ResourceExchanges
        """
        if i == 0:
            return [[]]
        if min_resource_index == source_resource.value:
            return self._trade_options_with_i_trades_and_min_resource_index(i, source_resource, min_resource_index + 1)
        if min_resource_index == LastResourceIndex or \
                (min_resource_index == LastResourceIndex - 1 and source_resource.value == LastResourceIndex):
            trade = ResourceExchange(source_resource=source_resource,
                                     target_resource=Resource(min_resource_index),
                                     count=i)
            return [[trade]]

        trades = []
        for min_resource_trade_count in range(i):
            partial_trades = self._trade_options_with_i_trades_and_min_resource_index(i - min_resource_trade_count,
                                                                                      source_resource,
                                                                                      min_resource_index + 1)
            if min_resource_trade_count != 0:  # We don't need moves where count is 0
                for partial_trade in partial_trades:
                    partial_trade.append(ResourceExchange(source_resource=source_resource,
                                                          target_resource=Resource(min_resource_index),
                                                          count=min_resource_trade_count))
            trades += partial_trades

        min_resource_only_trade = ResourceExchange(source_resource=source_resource,
                                                   target_resource=Resource(min_resource_index),
                                                   count=i)
        trades.append([min_resource_only_trade])
        return trades

    def _get_all_possible_development_cards_exposure_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        if not player.has_unexposed_development_card():
            return moves

        for dev_card_type in DevelopmentCard:
            if player.unexposed_development_cards[dev_card_type] == 0:  # player doesn't have this card
                continue
            for move in moves:
                new_move = copy.deepcopy(move)
                new_move.development_card_to_be_exposed = dev_card_type
                new_moves.append(new_move)
        # Knight
        knight_applied_moves, non_knight_applied_moves = [], []
        for move in new_moves:
            if move.development_card_to_be_exposed != DevelopmentCard.Knight or \
                            move.robber_placement_land != self.board.get_robber_land():
                non_knight_applied_moves.append(move)
                continue
            for land in self.board.get_lands_to_place_robber_on():
                new_move = copy.deepcopy(move)
                new_move.robber_placement_land = land
                knight_applied_moves.append(new_move)
        new_moves = knight_applied_moves + non_knight_applied_moves
        # year of plenty
        year_of_plenty_applied_moves = []
        moves_without_y_o_p = []
        for move in new_moves:
            if move.development_card_to_be_exposed == DevelopmentCard.YearOfPlenty:
                for two_cards in combinations_with_replacement(Resource, 2):
                    new_move = copy.deepcopy(move)
                    if two_cards[0] == two_cards[1]:  # same card twice
                        new_move.resources_updates[two_cards[0]] = 1
                        new_move.resources_updates[two_cards[1]] = 1
                    else:  # two different cards
                        new_move.resources_updates[two_cards[0]] = 2
                    year_of_plenty_applied_moves.append(new_move)
            else:
                moves_without_y_o_p.append(move)
        new_moves = moves_without_y_o_p + year_of_plenty_applied_moves
        # monopoly
        monopoly_applied_moves = []
        moves_without_monopoly = []
        for move in new_moves:
            if move.development_card_to_be_exposed == DevelopmentCard.Monopoly:
                for resource in Resource:
                    new_move = copy.deepcopy(move)
                    new_move.monopoly_card = resource
                    monopoly_applied_moves.append(new_move)
            else:
                moves_without_monopoly.append(move)
        new_moves = moves_without_monopoly + monopoly_applied_moves
        return moves + new_moves

    def _get_all_possible_paths_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if player.can_pave_road():  # optimization
                paths_options_with_duplicates = self._paths_options_up_to_i_chosen(player.amount_of_roads_can_afford())
                paths_options = set(frozenset(p) for p in paths_options_with_duplicates)
                for option in paths_options:
                    new_move = copy.deepcopy(move)
                    new_move.paths_to_be_paved = option
                    new_moves.append(new_move)
            self._unpretend_to_make_a_move(move)

        # RoadBuilding
        if player.unexposed_development_cards[DevelopmentCard.RoadBuilding] == 0:  # optimization
            return moves + new_moves
        return [move for move in moves + new_moves if
                len(move.paths_to_be_paved) >=
                2 * (move.development_card_to_be_exposed == DevelopmentCard.RoadBuilding)]  # c style

    def _paths_options_up_to_i_chosen(self, i) -> List[List[Path]]:
        """
        return all the options with up to i paths to be paved (duplications are possible!)
        the result (list of options) doesn't include the empty option (the option not to build any roads).
        :param i: Maximal number of options
        :return: List of List[Path] - list of valid 'paths_to_be_paved' options. returns [] in case of no valid option
        (Notice it's different from [[]] which is illegal)
        """
        if i == 0:
            return []

        player = self.get_current_player()
        paths_nearby = self.board.get_unpaved_paths_near_player(player)

        if i == 1:  # optimization
            return [[x] for x in paths_nearby]

        options = []
        for curr_path in paths_nearby:
            self.board.set_path(player, curr_path, Road.Paved)  # put on board
            options_given_curr_chosen = self._paths_options_up_to_i_chosen(i - 1)  # get all options  with curr
            assert options_given_curr_chosen != [[]]
            self.board.set_path(player, curr_path, Road.Unpaved)  # remove from board
            options.append([curr_path])  # curr only option
            for option in options_given_curr_chosen:  # generate an append all options including curr
                option.append(curr_path)
                options.append(option)
        return options

    def _get_all_possible_settlements_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            locations = self.board.get_settleable_locations_by_player(player)
            for i in range(1, player.amount_of_settlements_can_afford() + 1):
                settlement_options = self._locations_options_i_chosen_min_location_index(i, locations)
                for option in settlement_options:
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_settlements = option
                    new_moves.append(new_move)
            self._unpretend_to_make_a_move(move)
        return moves + new_moves

    def _get_all_possible_cities_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            locations = self.board.get_settlements_by_player(player)
            for i in range(1, player.amount_of_cities_can_afford() + 1):
                settlement_options = self._locations_options_i_chosen_min_location_index(i, locations)
                for option in settlement_options:
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_cities = option
                    new_moves.append(new_move)
            self._unpretend_to_make_a_move(move)
        return moves + new_moves

    def _locations_options_i_chosen_min_location_index(self, i: int, locations: List[Location],
                                                       min_location_index=0) -> List[List[Location]]:
        """
        returns a list of locations lists that represent locations choices
        :param i: number of locations to be chosen
        :param locations: the list of possible locations
        :param min_location_index: no need to set this value. used for the recursive implementation
        :return: List[List[Location]] s.t. each List[Location] represents an option to pick i
                                                                            locations from the provided locations
        """
        assert i > 0
        if (not locations) or min_location_index >= len(locations):
            return []
        if i > len(locations) - min_location_index:  # Not enough locations beyond index
            return []

        options_without_curr_location = self._locations_options_i_chosen_min_location_index(i, locations,
                                                                                            min_location_index + 1)
        if i == 1:
            options_without_curr_location.append([locations[min_location_index]])
            return options_without_curr_location
        options_with_curr_location = self._locations_options_i_chosen_min_location_index(i - 1, locations,
                                                                                         min_location_index + 1)
        for option_with_curr_location in options_with_curr_location:
            option_with_curr_location.append(locations[min_location_index])
        return options_with_curr_location + options_without_curr_location

    def _get_all_possible_development_cards_purchase_count_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if (player.has_resources_for_development_card() and
                        len(self._dev_cards) > move.development_cards_to_be_purchased_count):
                new_move = copy.deepcopy(move)
                new_move.development_cards_to_be_purchased_count += 1
                new_moves.append(new_move)
            self._unpretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_development_cards_purchase_count_moves(new_moves)

    def _get_all_possible_development_cards_purchase_options(
            self, cards_to_purchase_count: int,
            development_cards: List[DevelopmentCard] = [c for c in DevelopmentCard],
            purchased_cards: Dict[DevelopmentCard, int] = {cc: 0 for cc in DevelopmentCard},
            probability: float = 1.0) -> List[PurchaseOption]:

        if cards_to_purchase_count == 0:
            return [PurchaseOption(copy.deepcopy(purchased_cards), probability)]

        cards_that_can_be_purchased_count = sum(self._unexposed_dev_cards_counters[card] for card in development_cards)
        if cards_that_can_be_purchased_count < cards_to_purchase_count:
            return []

        card = development_cards[0]
        if self._unexposed_dev_cards_counters[card] == 0:
            return self._get_all_possible_development_cards_purchase_options(
                cards_to_purchase_count, development_cards[1:], purchased_cards, probability)

        without_card = self._get_all_possible_development_cards_purchase_options(
            cards_to_purchase_count, development_cards[1:], purchased_cards, probability)

        cards_left = sum(self._unexposed_dev_cards_counters[card] for card in DevelopmentCard)
        probability = probability * self._unexposed_dev_cards_counters[card] / float(cards_left)
        purchased_cards[card] += 1
        self._unexposed_dev_cards_counters[card] -= 1
        with_card = self._get_all_possible_development_cards_purchase_options(
            cards_to_purchase_count - 1, development_cards, purchased_cards, probability)
        purchased_cards[card] -= 1
        self._unexposed_dev_cards_counters[card] += 1

        return with_card + without_card

    def _pretend_to_make_a_move(self, move: CatanMove):
        player = self.get_current_player()
        player.update_resources(move.resources_updates, AbstractPlayer.add_resource)
        previous_robber_land_placement = self.board.get_robber_land()
        self.board.set_robber_land(move.robber_placement_land)
        move.robber_placement_land = previous_robber_land_placement
        if move.development_card_to_be_exposed == DevelopmentCard.RoadBuilding:
            self._apply_road_building_dev_card_side_effect(1)
        elif move.development_card_to_be_exposed == DevelopmentCard.Monopoly:
            assert move.monopoly_card is not None
            for other_player in self.players:
                if other_player is player:
                    continue
                resource = move.monopoly_card
                resource_count = other_player.get_resource_count(resource)
                move.monopoly_card_debt[other_player] = resource_count
                other_player.remove_resource(resource, resource_count)
                player.add_resource(resource, resource_count)
        if move.development_card_to_be_exposed is not None:
            player.expose_development_card(move.development_card_to_be_exposed)
            self._unexposed_dev_cards_counters[move.development_card_to_be_exposed] -= 1
            assert self._unexposed_dev_cards_counters[move.development_card_to_be_exposed] >= 0
        for exchange in move.resources_exchanges:
            player.trade_resources(exchange.source_resource, exchange.target_resource, exchange.count,
                                   self._calc_curr_player_trade_ratio(exchange.source_resource))
        for path in move.paths_to_be_paved:
            self.board.set_path(player, path, Road.Paved)
            player.remove_resources_and_piece_for_road()
        for loc1 in move.locations_to_be_set_to_settlements:
            self.board.set_location(player, loc1, Colony.Settlement)
            player.remove_resources_and_piece_for_settlement()
        for loc2 in move.locations_to_be_set_to_cities:
            self.board.set_location(player, loc2, Colony.City)
            player.remove_resources_and_piece_for_city()
        for count in range(0, move.development_cards_to_be_purchased_count):
            player.remove_resources_for_development_card()

    def _unpretend_to_make_a_move(self, move: CatanMove):
        player = self.get_current_player()
        for count in range(0, move.development_cards_to_be_purchased_count):
            player.add_resources_for_development_card()
        for loc2 in move.locations_to_be_set_to_cities:
            self.board.set_location(player, loc2, Colony.Settlement)
            player.add_resources_and_piece_for_city()
        for loc1 in move.locations_to_be_set_to_settlements:
            self.board.set_location(player, loc1, Colony.Uncolonised)
            player.add_resources_and_piece_for_settlement()
        for path in move.paths_to_be_paved:
            self.board.set_path(player, path, Road.Unpaved)
            player.add_resources_and_piece_for_road()
        for exchange in move.resources_exchanges:
            player.un_trade_resources(exchange.source_resource, exchange.target_resource, exchange.count,
                                      self._calc_curr_player_trade_ratio(exchange.source_resource))
        if move.development_card_to_be_exposed is not None:
            player.un_expose_development_card(move.development_card_to_be_exposed)
            self._unexposed_dev_cards_counters[move.development_card_to_be_exposed] += 1
        if move.development_card_to_be_exposed == DevelopmentCard.RoadBuilding:
            self._revert_road_building_dev_card_side_effect(1)
        elif move.development_card_to_be_exposed == DevelopmentCard.Monopoly:
            assert move.monopoly_card is not None
            for other_player in self.players:
                if other_player is player:
                    continue
                resource = move.monopoly_card
                resource_count = move.monopoly_card_debt[other_player]
                other_player.add_resource(resource, resource_count)
                player.remove_resource(resource, resource_count)
        robber_land_placement_to_undo = self.board.get_robber_land()  # this is done just in case, probably redundant
        self.board.set_robber_land(move.robber_placement_land)
        move.robber_placement_land = robber_land_placement_to_undo  # this is done just in case, probably redundant
        player.update_resources(move.resources_updates, AbstractPlayer.remove_resource)

    def _apply_road_building_dev_card_side_effect(self, count: int):
        """
        This method will add the resources needed for (count*2) roads. all moves that include exposing
        road building dev card and don't pave (count*2) roads will be considered as illegal moves.
        :param count: num of road building dev cards to be exposed
        """
        curr_player = self.get_current_player()
        # All the moves that expose the card and don't make count * 2 new roads are removed
        curr_player.add_resource(Resource.Brick, count * 2)
        curr_player.add_resource(Resource.Lumber, count * 2)

    def _revert_road_building_dev_card_side_effect(self, count: int):
        curr_player = self.get_current_player()
        curr_player.remove_resource(Resource.Brick, count * 2)
        curr_player.remove_resource(Resource.Lumber, count * 2)

    initialisation_resources = ResourceAmounts().add_road().add_settlement()

    def _get_initialisation_moves(self):
        player = self.get_current_player()
        assert sum(player.resources.values()) == 0
        assert self.is_initialisation_phase()

        player.update_resources(ResourceAmounts.settlement, AbstractPlayer.add_resource)
        moves = self._add_settlements_to_initialisation_moves()

        player.update_resources(ResourceAmounts.road, AbstractPlayer.add_resource)
        moves = self._add_roads_to_initialisation_moves(moves)

        # remove resources given to player now, and give it to him when the move will actually be made.
        # that way there's no side-effect to this method, and 'revert' the move would be easy.
        # it also simplifies the way a user gets
        is_second_initialisation_move = self.board.get_colonies_score(player) == 1
        player.update_resources(CatanState.initialisation_resources, AbstractPlayer.remove_resource)
        for move in moves:
            move.resources_updates = CatanState.initialisation_resources
            if is_second_initialisation_move:
                move.resources_updates = copy.deepcopy(move.resources_updates)
                initial_resources = self.board.get_surrounding_resources(move.locations_to_be_set_to_settlements[0])
                for resource in initial_resources:
                    move.resources_updates[resource] += 1

        return moves

    def _add_roads_to_initialisation_moves(self, moves):
        moves = [move for move in self._get_all_possible_paths_moves(moves) if move not in moves]
        assert all([(len(move.resources_exchanges) == 0 and
                     move.development_card_to_be_exposed is None and
                     len(move.paths_to_be_paved) == 1 and
                     len(move.locations_to_be_set_to_settlements) == 1 and
                     len(move.locations_to_be_set_to_cities) == 0 and
                     move.development_cards_to_be_purchased_count == 0 and
                     not move.did_get_largest_army_card and
                     not move.did_get_longest_road_card and
                     move.robber_placement_land == self.board.get_robber_land())
                    for move in moves])

        def valid_path_paved(move):
            path = next(iter(move.paths_to_be_paved))
            settlement = next(iter(move.locations_to_be_set_to_settlements))
            return settlement in path

        moves = [move for move in moves if valid_path_paved(move)]
        return moves

    def _add_settlements_to_initialisation_moves(self):
        empty_move = CatanMove(self.board.get_robber_land())
        moves = [empty_move]
        moves = self._get_all_possible_settlements_moves(moves)
        moves.remove(empty_move)
        for move in moves:
            assert len(move.resources_exchanges) == 0
            assert move.development_card_to_be_exposed is None
            assert len(move.paths_to_be_paved) == 0
            assert len(move.locations_to_be_set_to_settlements) == 1
            assert len(move.locations_to_be_set_to_cities) == 0
            assert move.development_cards_to_be_purchased_count == 0
            assert not move.did_get_largest_army_card
            assert not move.did_get_longest_road_card
            assert (move.robber_placement_land == self.board.get_robber_land() or move.robber_placement_land is None)
        return moves
