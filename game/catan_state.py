import copy
from collections import namedtuple
from typing import List, Tuple
from game.board import Board, Resource, Harbor, FirsResourceIndex, LastResourceIndex, ResourceAmounts
from game.pieces import Colony, Road
from algorithms.abstract_state import AbstractState, AbstractMove
from game.abstract_player import AbstractPlayer
from game.development_cards import DevelopmentCard, LastDevCardIndex, FirstDevCardIndex
from train_and_test import logger
import numpy as np

ResourceExchange = namedtuple('ResourceExchange', ['source_resource', 'target_resource', 'count'])


class CatanMove(AbstractMove):
    def __init__(self, robber_placement_land=None):
        self.resources_exchanges = []
        self.development_cards_to_be_exposed = []
        self.paths_to_be_paved = []
        self.locations_to_be_set_to_settlements = []
        self.locations_to_be_set_to_cities = []
        self.development_cards_to_be_purchased_count = 0
        self.did_get_largest_army_card = False
        self.did_get_longest_road_card = False
        self.robber_placement_land = robber_placement_land
        self.monopoly_card = None
        self.resources_updates = {}

    def is_doing_anything(self):
        """
        indicate whether anything is done in this move
        :return: True if anything is done in this move, False otherwise
        """
        return (len(self.resources_exchanges) != 0 or
                len(self.development_cards_to_be_exposed) != 0 or
                len(self.paths_to_be_paved) != 0 or
                len(self.locations_to_be_set_to_settlements) != 0 or
                len(self.locations_to_be_set_to_cities) != 0 or
                self.development_cards_to_be_purchased_count != 0)

    def apply(self, state):
        """
        apply the move in the given state
        :param state: the state to apply the moves on
        :return: None
        """
        assert isinstance(state, CatanState)

        # this does almost everything, the rest is done in this method
        state.pretend_to_make_a_move(self)

        player = state.get_current_player()
        # for card in self.development_cards_to_be_exposed:
        #       TODO apply side effect from card
        # TODO figure out when is it actually done
        # for _ in range(self.development_cards_to_be_purchased_count):
        #     player.add_unexposed_development_card(state.pop_development_card())

    def revert(self, state):
        """
        revert the move in the given state
        :param state: the state to revert the moves on
        :return: None
        """
        assert isinstance(state, CatanState)

        # this does almost everything, the rest is done in this method
        state.revert_pretend_to_make_a_move(self)

        player = state.get_current_player()
        # for card in self.development_cards_to_be_exposed:
        #       TODO revert side effect from card
        # TODO figure out when is it actually done
        # for count in range(self.development_cards_to_be_purchased_count):
        #       TODO add purchase card mechanism here. should apply : player.add_unexposed_development_card(zzzzzz)


class RandomMove(AbstractMove):
    def __init__(self, rolled_dice: int, state):
        self._rolled_dice = rolled_dice
        self._state = state
        self._previous_rolled_dice = self._state.current_dice_number
        self._resources_by_players = {}

    def apply(self):
        if self._state.is_initialization_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.remove_resource
            self._resources_by_players = {player: player.choose_resources_to_drop() for player in self._state.players}
        else:
            update_method = AbstractPlayer.add_resource
            self._resources_by_players = self._state.board.get_players_to_resources_by_dice_value(self._rolled_dice)
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._rolled_dice

    def revert(self):
        if self._state.is_initialization_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.add_resource
        else:
            update_method = AbstractPlayer.remove_resource
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._previous_rolled_dice


class CatanState(AbstractState):
    def __init__(self, players: List[AbstractPlayer], seed=None):
        if seed is not None and not (0 <= seed < 1):
            logger.error('{parameter_name} should be in the range [0,1). treated as if no {parameter_name}'
                         ' was sent'.format(parameter_name=CatanState.__init__.__code__.co_varnames[2]))
            seed = None

        numpy_seed = seed if seed is None else int(seed * 10)
        random_state = np.random.RandomState(seed=numpy_seed)
        self._random_choice = random_state.choice

        self.players = players
        self.board = Board(seed)

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
        if self.is_initialization_phase():
            return self._get_initialisation_moves()

        if self.current_dice_number != 7:
            empty_move = CatanMove()
            moves = [empty_move]
        else:
            moves = [CatanMove(land) for land in self.board.get_lands_to_place_robber_on()]
        moves = self._get_all_possible_development_cards_exposure_moves(moves)
        # _get_all_possible_trade_moves is assuming it's after dev_cards moves and nothing else
        moves = self._get_all_possible_trade_moves(moves)
        moves = self._get_all_possible_paths_moves(moves)
        moves = self._get_all_possible_settlements_moves(moves)
        moves = self._get_all_possible_cities_moves(moves)
        moves = self._get_all_possible_development_cards_purchase_moves(moves)
        return moves

    def is_initialization_phase(self):
        return self.board.get_colonies_score(self.get_current_player()) < 2

    def make_move(self, move: CatanMove):
        """makes specified move"""
        move.apply(self)

        self._update_longest_road(move)
        self._update_largest_army(move)

        self._current_player_index = (self._current_player_index + 1) % len(self.players)

    def unmake_move(self, move: CatanMove):
        """reverts specified move"""
        self._current_player_index = (self._current_player_index - 1) % len(self.players)

        move.revert(self)

        self._revert_update_longest_road(move)
        self._revert_update_largest_army(move)

    def get_current_player(self):
        """returns the player that should play next"""
        return self.players[self._current_player_index]

    numbers_to_probabilities = {}

    for i, p in zip(range(2, 7), range(1, 6)):
        numbers_to_probabilities[i] = p / 36
        numbers_to_probabilities[14 - i] = p / 36
    numbers_to_probabilities[7] = 6 / 36

    def get_numbers_to_probabilities(self):
        return CatanState.numbers_to_probabilities

    def pop_development_card(self) -> DevelopmentCard:
        return self._dev_cards.pop()

    def throw_dice(self, rolled_dice_number: int = None):
        """throws the dice (if no number is given), and gives players the cards they need
        :return: the dice throwing result (a number in the range [2,12])
        """
        if rolled_dice_number is None:
            rolled_dice_number = self._random_choice(a=list(CatanState.numbers_to_probabilities.keys()),
                                                     p=list(CatanState.numbers_to_probabilities.values()))
        move = RandomMove(rolled_dice_number, self)
        move.apply()
        return move

    def unthrow_dice(self, move: RandomMove):
        """reverts the dice throwing and cards giving
        :param move: the random move to revert
        :return: None
        """
        move.revert()

    def _update_longest_road(self, move: CatanMove):
        # TODO this can be converted to something done in CatanMove
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
        # TODO this can be converted to something done in CatanMove
        if move.development_cards_to_be_exposed.count(DevelopmentCard.Knight) == 0:
            return

        player_with_largest_army, size_threshold = self._get_largest_army_player_and_size()
        army_size = self.get_current_player().get_exposed_knights_count()

        if army_size > size_threshold:
            self._player_with_largest_army.append((self.get_current_player(), army_size))
            move.did_get_largest_army_card = True

    def _revert_update_largest_army(self, move: CatanMove):
        if move.did_get_largest_army_card:
            self._player_with_largest_army.pop()

    def _get_longest_road_player_and_length(self) -> Tuple[AbstractPlayer, int]:
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

    KnightCardsCount = int

    def _get_largest_army_player_and_size(self) -> Tuple[AbstractPlayer, KnightCardsCount]:
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
            for i in range(int(player.get_resource_count(source_resource) / self._calc_curr_player_trade_ratio(
                    source_resource))):
                no_dev_card_side_effect_trades = no_dev_card_side_effect_trades + \
                                                 self._trades_permutations_i_cards_min_resource_index(
                                                     i, source_resource, FirsResourceIndex)

        for move in moves:
            # assuming it's after dev_cards moves and nothing else (bad programming but better performance)
            if (DevelopmentCard.YearOfPlenty not in move.development_cards_to_be_exposed) and \
                    (DevelopmentCard.Monopoly not in move.development_cards_to_be_exposed):
                self.pretend_to_make_a_move(move)
                for source_resource in Resource:
                    for i in range(int(player.get_resource_count(source_resource) /
                                               self._calc_curr_player_trade_ratio(source_resource))):
                        for trades in self._trades_permutations_i_cards_min_resource_index(i, source_resource,
                                                                                           FirsResourceIndex):
                            new_move = copy.deepcopy(move)
                            new_move.resources_exchanges = trades
                            new_moves.append(new_move)
                self.revert_pretend_to_make_a_move(move)
            else:
                for trades in no_dev_card_side_effect_trades:
                    new_move = copy.deepcopy(move)
                    new_move.resources_exchanges = trades
                    new_moves.append(new_move)

        return moves + new_moves

    def _trades_permutations_i_cards_min_resource_index(self, i, source_resource, min_resource_index) \
            -> List[List[ResourceExchange]]:
        """
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
            return []
        if min_resource_index == source_resource.value:
            return self._trades_permutations_i_cards_min_resource_index(i, source_resource, min_resource_index + 1)
        if min_resource_index == LastResourceIndex or \
                (min_resource_index == LastResourceIndex - 1 and source_resource.value == LastResourceIndex):
            trade = ResourceExchange(source_resource=source_resource,
                                     target_resource=Resource(min_resource_index),
                                     count=i)
            return [[trade]]

        trades = []
        for min_resource_trade_count in range(i):
            partial_trades = self._trades_permutations_i_cards_min_resource_index(i - min_resource_trade_count,
                                                                                  source_resource,
                                                                                  min_resource_index + 1)
            for partial_trade in partial_trades:
                partial_trade.append(ResourceExchange(source_resource=source_resource,
                                                      target_resource=Resource(min_resource_index),
                                                      count=min_resource_trade_count))
            trades = trades + partial_trades

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
        expose_options = self._get_dev_card_exposure_moves_min_card_index(FirstDevCardIndex)
        for move in moves:
            for expose_option in expose_options:
                new_move = copy.deepcopy(move)
                new_move.development_cards_to_be_exposed = expose_option
                new_moves.append(new_move)
        knight_applied_moves, non_knight_applied_moves = [], []
        for move in new_moves:
            if (DevelopmentCard.Knight not in move.development_cards_to_be_exposed
               or move.robber_placement_land != self.board.get_robber_land()):
                non_knight_applied_moves.append(move)
                continue
            for land in self.board.get_lands_to_place_robber_on():
                new_move = copy.deepcopy(move)
                new_move.robber_placement_land = land
                knight_applied_moves.append(new_move)
        new_moves = knight_applied_moves + non_knight_applied_moves
        return moves + new_moves

    def _get_dev_card_exposure_moves_min_card_index(self, min_dev_card_index) -> List[List[DevelopmentCard]]:
        if min_dev_card_index > LastDevCardIndex:
            return [[]]
        player = self.get_current_player()
        unexposed = player.get_unexposed_development_cards()
        curr_card = DevelopmentCard(min_dev_card_index)
        if unexposed[curr_card] == 0:
            return self._get_dev_card_exposure_moves_min_card_index(min_dev_card_index + 1)

        curr_card_expose_options = []
        for i in range(unexposed[curr_card]):
            curr_card_expose_options.append([curr_card for _ in range(i)])

        later_cards_expose_options = self._get_dev_card_exposure_moves_min_card_index(min_dev_card_index + 1)
        res = []
        for curr_card_expose_option in curr_card_expose_options:
            for later_cards_expose_option in later_cards_expose_options:
                res.append(curr_card_expose_option + later_cards_expose_option)
        return res

    def _get_all_possible_paths_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if player.can_pave_road():
                for path_nearby in self.board.get_unpaved_paths_near_player(player):
                    new_move = copy.deepcopy(move)
                    new_move.paths_to_be_paved.append(path_nearby)
                    new_moves.append(new_move)
            if (DevelopmentCard.RoadBuilding in move.development_cards_to_be_exposed) and \
                    (len(move.paths_to_be_paved) < 2):  # applying side effect of dev card
                moves.remove(move)
            self.revert_pretend_to_make_a_move(move)

        if not new_moves:  # End of recursion
            return moves
        players_road_building_dev_cards = player.unexposed_development_cards[DevelopmentCard.RoadBuilding]
        if players_road_building_dev_cards > 0:  # optimization
            moves_corresponding_to_dev_cards = [
                x for x in moves if not ((DevelopmentCard.RoadBuilding in x.development_cards_to_be_exposed) and
                                         (len(x.paths_to_be_paved) < 2 * players_road_building_dev_cards))]
        else:
            moves_corresponding_to_dev_cards = moves
        return moves_corresponding_to_dev_cards + self._get_all_possible_paths_moves(new_moves)

    def _get_all_possible_settlements_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if player.can_settle_settlement():
                for settleable_location in self.board.get_settleable_locations_by_player(player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_settlements.append(settleable_location)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_settlements_moves(new_moves)

    def _get_all_possible_cities_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if player.can_settle_city():
                for cityable_location in self.board.get_settlements_by_player(player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_cities.append(cityable_location)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_cities_moves(new_moves)

    def _get_all_possible_development_cards_purchase_moves(self, moves: List[CatanMove]) -> List[CatanMove]:
        player = self.get_current_player()
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if (player.has_resources_for_development_card() and
                        len(self._dev_cards) > move.development_cards_to_be_purchased_count):
                new_move = copy.deepcopy(move)
                new_move.development_cards_to_be_purchased_count += 1
                new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_development_cards_purchase_moves(new_moves)

    def pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        if move.robber_placement_land is None:
            move.robber_placement_land = self.board.get_robber_land()
        player = self.get_current_player()
        player.update_resources(move.resources_updates, AbstractPlayer.add_resource)
        previous_robber_land_placement = self.board.get_robber_land()
        self.board.set_robber_land(move.robber_placement_land)
        move.robber_placement_land = previous_robber_land_placement
        for card in move.development_cards_to_be_exposed:
            self._apply_dev_card_side_effect(card)
            player.expose_development_card(card)
        for exchange in move.resources_exchanges:
            player.trade_resources(exchange.source_resource, exchange.target_resource, exchange.count)
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
            # TODO add purchase card mechanism here. should apply : player.add_unexposed_development_card(zzzzzz)
            player.remove_resources_for_development_card()

    def revert_pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        player = self.get_current_player()
        for count in range(0, move.development_cards_to_be_purchased_count):
            # TODO add purchase card mechanism here. should apply : player.add_unexposed_development_card(zzzzzz)
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
            player.un_trade_resources(exchange.source_resource, exchange.target_resource, exchange.count)
        for card in move.development_cards_to_be_exposed:
            self._revert_dev_card_side_effect(card)
            player.un_expose_development_card(card)
        robber_land_placement_to_undo = self.board.get_robber_land()  # this is done just in case, probably redundant
        self.board.set_robber_land(move.robber_placement_land)
        move.robber_placement_land = robber_land_placement_to_undo  # this is done just in case, probably redundant
        player.update_resources(move.resources_updates, AbstractPlayer.remove_resource)

    def _apply_dev_card_side_effect(self, card: DevelopmentCard):
        curr_player = self.get_current_player()
        if card is DevelopmentCard.Knight:
            # TODO Arye should implement
            pass
        elif card is DevelopmentCard.RoadBuilding:
            # All the moves that expose the card and don't make 2 new roads are removed
            curr_player.add_resource(Resource.Brick, 2)
            curr_player.add_resource(Resource.Lumber, 2)
        elif card is DevelopmentCard.Monopoly:
            # TODO implement
            pass
        elif card is DevelopmentCard.YearOfPlenty:
            # TODO implement
            pass

    def _revert_dev_card_side_effect(self, card: DevelopmentCard):
        curr_player = self.get_current_player()
        if card is DevelopmentCard.Knight:
            # TODO Arye should implement
            pass
        elif card is DevelopmentCard.RoadBuilding:
            curr_player.remove_resource(Resource.Brick, 2)
            curr_player.remove_resource(Resource.Lumber, 2)
        elif card is DevelopmentCard.Monopoly:
            # TODO implement
            pass
        elif card is DevelopmentCard.YearOfPlenty:
            # TODO implement
            pass

    initialisation_resources = ResourceAmounts().add_road().add_settlement()

    def _get_initialisation_moves(self):
        player = self.get_current_player()
        assert sum(player.resources.values()) == 0

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
                     len(move.development_cards_to_be_exposed) == 0 and
                     len(move.paths_to_be_paved) == 1 and
                     len(move.locations_to_be_set_to_settlements) == 1 and
                     len(move.locations_to_be_set_to_cities) == 0 and
                     move.development_cards_to_be_purchased_count == 0 and
                     not move.did_get_largest_army_card and
                     not move.did_get_longest_road_card and
                     move.robber_placement_land == self.board.get_robber_land())
                    for move in moves])

        def valid_path_paved(move):
            path = move.paths_to_be_paved[0]
            settlement = move.locations_to_be_set_to_settlements[0]
            return settlement in path

        moves = [move for move in moves if valid_path_paved(move)]
        return moves

    def _add_settlements_to_initialisation_moves(self):
        empty_move = CatanMove()
        moves = [empty_move]
        moves = self._get_all_possible_settlements_moves(moves)
        moves.remove(empty_move)
        assert all([(len(move.resources_exchanges) == 0 and
                     len(move.development_cards_to_be_exposed) == 0 and
                     len(move.paths_to_be_paved) == 0 and
                     len(move.locations_to_be_set_to_settlements) == 1 and
                     len(move.locations_to_be_set_to_cities) == 0 and
                     move.development_cards_to_be_purchased_count == 0 and
                     not move.did_get_largest_army_card and
                     not move.did_get_longest_road_card and
                     move.robber_placement_land == self.board.get_robber_land()) for move in moves])
        return moves
