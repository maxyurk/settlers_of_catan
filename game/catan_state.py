import copy
import random
from typing import List, Callable, Tuple
from game.board import Board, Resource
from game.pieces import Colony, Road
from algorithms.abstract_state import AbstractState, AbstractMove
from game.abstract_player import AbstractPlayer
from game.development_cards import DevelopmentCard


class CatanMove(AbstractMove):
    def __init__(self):
        # TODO add resource exchange mechanism
        self.development_cards_to_be_exposed = []
        self.paths_to_be_paved = []
        self.locations_to_be_set_to_settlements = []
        self.locations_to_be_set_to_cities = []
        self.development_cards_to_be_purchased_count = 0
        self.did_get_largest_army_card = False
        self.did_get_longest_road_card = False

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

        curr_player = state.get_current_player()
        # for card in self.development_cards_to_be_exposed:
        #       TODO revert side effect from card
        # TODO figure out when is it actually done
        # for count in range(self.development_cards_to_be_purchased_count):
        #       TODO add purchase card mechanism here. should apply : curr_player.add_unexposed_development_card(zzzzzz)


class CatanState(AbstractState):
    def __init__(self, players: List[AbstractPlayer]):
        self._players = players
        self._current_player_index = 0
        self._board = Board()

        self._dev_cards = [DevelopmentCard.Knight] * 15 +\
                          [DevelopmentCard.VictoryPoint] * 5 +\
                          [DevelopmentCard.RoadBuilding,
                           DevelopmentCard.Monopoly,
                           DevelopmentCard.YearOfPlenty] * 2
        random.shuffle(self._dev_cards)

        # we must preserve these in the state, since it's possible a
        # player has one of the special cards, while some-one has the
        # same amount of knights-cards used/longest road length
        # i.e when player 1 paved 5 roads, and player too as-well,
        # but only after player 1.
        self._player_with_largest_army = []
        self._player_with_longest_road = []

    # TODO we should probably extract a get_scores_by_player method from here
    def is_final(self):
        """
        check if the current state in the game is final or not
        Returns:
            bool: indicating whether the current state is a final one
        """
        players_points_count = {player: self._board.get_colonies_score(player)
                                for player in self._players}

        player, _ = self._get_largest_army_player_and_size()
        if player is not None:
            players_points_count[player] += 2

        player, _ = self._get_longest_road_player_and_length()
        if player is not None:
            players_points_count[player] += 2

        for player in self._players:
            players_points_count[player] += player.get_victory_point_development_cards_count()

        highest_score = max(players_points_count.values())
        return highest_score >= 10

    def get_next_moves(self):
        """computes the next moves available from the current state
        Returns:
            List of AbstractMove: a list of the next moves
        """
        empty_move = CatanMove()
        moves = [empty_move]
        # TODO add resource exchange mechanism here
        moves = self._get_all_possible_development_cards_exposure_moves(moves)
        moves = self._get_all_possible_paths_moves(moves)
        moves = self._get_all_possible_settlements_moves(moves)
        moves = self._get_all_possible_cities_moves(moves)
        moves = self._get_all_possible_development_cards_purchase_moves(moves)
        return moves

    def make_move(self, move: CatanMove):
        """makes specified move"""
        # TODO when knight card is used, check if largest army has changed
        move.apply(self)

        if len(move.paths_to_be_paved) != 0:
            longest_road_length = self._board.get_longest_road_length_of_player(self.get_current_player())
            _, length_threshold = self._get_longest_road_player_and_length()

            if longest_road_length > length_threshold:
                self._player_with_longest_road.append(((self.get_current_player()), longest_road_length))
                move.did_get_largest_army_card = True

        self._current_player_index = (self._current_player_index + 1) % len(self._players)

    def unmake_move(self, move: CatanMove):
        """reverts specified move"""

        move.revert(self)

        if move.did_get_largest_army_card:
            self._player_with_longest_road.pop()

        self._current_player_index = (self._current_player_index - 1) % len(self._players)

    def get_current_player(self):
        """returns the player that should play next"""
        return self._players[self._current_player_index]

    numbers_to_probabilities = {}
    for i, p in zip(range(2, 7), range(1, 6)):
        numbers_to_probabilities[i] = p / 36
        numbers_to_probabilities[14 - i] = p / 36
    numbers_to_probabilities[7] = 6 / 36

    def get_numbers_to_probabilities(self):
        return CatanState.numbers_to_probabilities

    def pop_development_card(self) -> DevelopmentCard:
        return self._dev_cards.pop()

    def throw_dice(self, rolled_dice_number: int=None):
        """throws the dice (if no number is given), and gives players the cards they need
        :return: the dice throwing result (a number in the range [2,12])
        """
        if rolled_dice_number is None:
            rolled_dice_number = random.randint(2, 12)
        self._on_thrown_dice_update_resources(rolled_dice_number, AbstractPlayer.add_resource)
        # TODO handle moving robber when rolled 7
        return rolled_dice_number

    def unthrow_dice(self, rolled_dice_number):
        """reverts the dice throwing and cards giving
        :param rolled_dice_number: the number to undo it's cards giving
        :return: None
        """
        # TODO handle unmoving robber when rolled 7
        self._on_thrown_dice_update_resources(rolled_dice_number, AbstractPlayer.remove_resource)

    def _on_thrown_dice_update_resources(
            self, rolled_dice_number,
            add_or_remove_resource: Callable[[AbstractPlayer, Resource, int], None]):
        """
        auxiliary method to give/take the cards need for specified number
        :param rolled_dice_number: the number to give/take card by
        :param add_or_remove_resource: Callable[[AbstractPlayer, Resource, int], None]
        a function that gives/takes from the player the given amount of the given resource
        it should either be AbstractPlayer.add_resource, or AbstractPlayer.remove_resource
        :return: None
        """
        if rolled_dice_number == 7:
            return

        players_to_resources = \
            self._board.get_players_to_resources_by_number(rolled_dice_number)

        for player, resources_to_amount in players_to_resources.items():
            for resource, resource_amount in resources_to_amount.items():
                add_or_remove_resource(player, resource, resource_amount)

    RoadLength = int

    def _get_longest_road_player_and_length(self) -> Tuple[AbstractPlayer, RoadLength]:
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
        if not self._player_with_largest_army:
            return None, 0
        return self._player_with_largest_army[-1]

    def _get_all_possible_development_cards_exposure_moves(self, moves: List[CatanMove]):
        curr_player = self._players[self._current_player_index]
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if curr_player.has_unexposed_development_card():
                for unexposed_development_card in curr_player.get_unexposed_development_cards():
                    new_move = copy.deepcopy(move)
                    new_move.development_cards_to_be_exposed.append(unexposed_development_card)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_development_cards_exposure_moves(moves)

    def _get_all_possible_paths_moves(self, moves: List[CatanMove]):
        curr_player = self._players[self._current_player_index]
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if curr_player.can_pave_road():
                for path_nearby in self._board.get_unpaved_paths_near_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.paths_to_be_paved.append(path_nearby)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_paths_moves(new_moves)

    def _get_all_possible_settlements_moves(self, moves: List[CatanMove]):
        curr_player = self._players[self._current_player_index]
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if curr_player.can_settle_settlement():
                for settleable_location in self._board.get_settleable_locations_by_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_settlements.append(settleable_location)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_settlements_moves(new_moves)

    def _get_all_possible_cities_moves(self, moves: List[CatanMove]):
        curr_player = self._players[self._current_player_index]
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if curr_player.can_settle_city():
                for cityable_location in self._board.get_settlements_by_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_cities.append(cityable_location)
                    new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        return moves + self._get_all_possible_cities_moves(new_moves)

    def _get_all_possible_development_cards_purchase_moves(self, moves: List[CatanMove]):
        curr_player = self.get_current_player()
        new_moves = []
        for move in moves:
            self.pretend_to_make_a_move(move)
            if (curr_player.has_resources_for_development_card() and
                    len(self._dev_cards) > move.development_cards_to_be_purchased_count):
                new_move = copy.deepcopy(move)
                new_move.development_cards_to_be_purchased_count += 1
                new_moves.append(new_move)
            self.revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return moves + self._get_all_possible_development_cards_purchase_moves(new_moves)

    def pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        player = self.get_current_player()
        for card in move.development_cards_to_be_exposed:
            # TODO apply side effect from card
            player.expose_development_card(card)
        for path in move.paths_to_be_paved:
            self._board.set_path(player, path, Road.Paved)
            player.remove_resources_for_road()
        for loc1 in move.locations_to_be_set_to_settlements:
            self._board.set_location(player, loc1, Colony.Settlement)
            player.remove_resources_for_settlement()
        for loc2 in move.locations_to_be_set_to_cities:
            self._board.set_location(player, loc2, Colony.City)
            player.remove_resources_for_city()
        for count in range(0, move.development_cards_to_be_purchased_count):

            # TODO add purchase card mechanism here. should apply : curr_player.add_unexposed_development_card(zzzzzz)
            player.remove_resources_for_development_card()

    def revert_pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        player = self.get_current_player()
        for card in move.development_cards_to_be_exposed:
            # TODO revert side effect from card
            player.un_expose_development_card(card)
        for path in move.paths_to_be_paved:
            self._board.set_path(player, path, Road.Unpaved)
            player.add_resources_for_road()
        for loc1 in move.locations_to_be_set_to_settlements:
            self._board.set_location(player, loc1, Colony.Uncolonised)
            player.add_resources_for_settlement()
        for loc2 in move.locations_to_be_set_to_cities:
            self._board.set_location(player, loc2, Colony.Uncolonised)
            player.add_resources_for_city()
        for count in range(0, move.development_cards_to_be_purchased_count):
            # TODO add purchase card mechanism here. should apply : curr_player.add_unexposed_development_card(zzzzzz)
            player.add_resources_for_development_card()
