import copy
import random
from typing import List, Callable
from game.board import Board, Resource, Road, Colony
from algorithms.abstract_state import AbstractState, AbstractMove
from game.abstract_player import AbstractPlayer
from game.development_cards import DevelopmentCard


class CatanState(AbstractState):
    def __init__(self, players: List[AbstractPlayer]):
        self.players = players
        self.current_player_index = 0
        self.board = Board()

        self.dev_cards = []
        for card in DevelopmentCard:
            self.dev_cards += [card] * card.value
        random.shuffle(self.dev_cards)

        # we must preserve these in the state, since it's possible a
        # player has one of the special cards, while some-one has the
        # same amount of knights-cards used/longest road length
        # i.e when player 1 paved 5 roads, and player too as-well,
        # but only after player 1.
        self.player_with_largest_army = None
        self.player_with_longest_road = None

    def is_final(self):
        """
        check if the current state in the game is final or not
        Returns:
            bool: indicating whether the current state is a final one
        """
        players_points_count = {player: self.board.get_colonies_score(player)
                                for player in self.players}
        if self.player_with_largest_army is not None:
            players_points_count[self.player_with_largest_army] += 2
        if self.player_with_longest_road is not None:
            players_points_count[self.player_with_longest_road] += 2
        for player in self.players:
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

    def make_move(self, move: AbstractMove):
        """makes specified move"""
        # TODO remember to go to next player. current_player_index = current_player_index+1%len of list
        # TODO when road is paved, check if longest road has changed
        # TODO when knight card is used, check if largest army has changed
        pass

    def unmake_move(self, move: AbstractMove):
        """reverts specified move"""
        pass

    def get_current_player(self):
        """returns the player that should play next"""
        return self.players[self.current_player_index]
        pass

    def throw_dice(self):
        """throws the dice, and gives players the cards they need
        :return: the dice throwing result (a number in the range [2,12])
        """
        rolled_dice_number = random.randint(2, 12)
        self._on_thrown_dice(rolled_dice_number, AbstractPlayer.add_resource)

        return rolled_dice_number

    def unthrow_dice(self, rolled_dice_number):
        """reverts the dice throwing and cards giving
        :param rolled_dice_number: the number to undo it's cards giving
        :return: None
        """
        self._on_thrown_dice(rolled_dice_number, AbstractPlayer.remove_resource)

    def _on_thrown_dice(self, rolled_dice_number,
                        add_or_remove_resource: Callable[[AbstractPlayer, Resource, int], None]):
        """
        auxilary method to give/take the cards need for specified number
        :param rolled_dice_number: the number to give/take card by
        :param add_or_remove_resource: Callable[[AbstractPlayer, Resource, int], None]
        a function that gives/takes from the player the given amount of the given resource
        it should either be AbstractPlayer.add_resource, or AbstractPlayer.remove_resource
        :return: None
        """
        players_to_resources = \
            self.board.get_players_to_resources_by_number(rolled_dice_number)

        for player, resources_to_amount in players_to_resources.items():
            for resource, resource_amount in resources_to_amount.items():
                add_or_remove_resource(player, resource, resource_amount)

    def _get_all_possible_development_cards_exposure_moves(self, moves: List[CatanMove]):
        curr_player = self.players[self.current_player_index]
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if curr_player.has_unexposed_development_card():
                for unexposed_development_card in curr_player.get_unexposed_development_cards():
                    new_move = copy.deepcopy(move)
                    new_move.development_cards_to_be_exposed.append(unexposed_development_card)
                    new_moves.append(new_move)
            self._revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_development_cards_exposure_moves(moves)

    def _get_all_possible_paths_moves(self, moves: List[CatanMove]):
        curr_player = self.players[self.current_player_index]
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if curr_player.has_resources_for_road():
                for path_nearby in self.board.get_unpaved_paths_near_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.paths_to_be_paved.append(path_nearby)
                    new_moves.append(new_move)
            self._revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_paths_moves(moves)

    def _get_all_possible_settlements_moves(self, moves: List[CatanMove]):
        curr_player = self.players[self.current_player_index]
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if curr_player.has_resources_for_settlement():
                for settleable_location in self.board.get_settleable_locations_by_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_settlements.append(settleable_location)
                    new_moves.append(new_move)
            self._revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_settlements_moves(moves)

    def _get_all_possible_cities_moves(self, moves: List[CatanMove]):
        curr_player = self.players[self.current_player_index]
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if curr_player.has_resources_for_city():
                for cityable_location in self.board.get_settlements_by_player(curr_player):
                    new_move = copy.deepcopy(move)
                    new_move.locations_to_be_set_to_cities.append(cityable_location)
                    new_moves.append(new_move)
            self._revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_cities_moves(moves)

    def _get_all_possible_development_cards_purchase_moves(self, moves: List[CatanMove]):
        curr_player = self.players[self.current_player_index]
        new_moves = []
        for move in moves:
            self._pretend_to_make_a_move(move)
            if curr_player.has_resources_for_development_card():
                new_move = copy.deepcopy(move)
                new_move.development_cards_to_be_purchased_count += 1
                new_moves.append(new_move)
            self._revert_pretend_to_make_a_move(move)
        if not new_moves:  # End of recursion
            return moves
        moves.extend(new_moves)
        return self._get_all_possible_development_cards_purchase_moves(moves)

    def _pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        curr_player = self.players[self.current_player_index]
        for card in move.development_cards_to_be_exposed:
            # TODO apply side effect from card
            curr_player.expose_development_card(card)
        for path in move.paths_to_be_paved:
            self.board.set_path(curr_player, path, Road.Paved)
            curr_player.remove_resources_for_road()
        for loc1 in move.locations_to_be_set_to_settlements:
            self.board.set_location(curr_player, loc1, Colony.Settlement)
            curr_player.remove_resources_for_settlement()
        for loc2 in move.locations_to_be_set_to_cities:
            self.board.set_location(curr_player, loc2, Colony.City)
            curr_player.remove_resources_for_city()
        for count in range(0, move.development_cards_to_be_purchased_count):
            # TODO add purchase card mechanism here. should apply : curr_player.add_unexposed_development_card(zzzzzz)
            curr_player.remove_resources_for_development_card()

    def _revert_pretend_to_make_a_move(self, move: CatanMove):
        # TODO add resource exchange mechanism
        curr_player = self.players[self.current_player_index]
        for card in move.development_cards_to_be_exposed:
            # TODO revert side effect from card
            curr_player.un_expose_development_card(card)
        for path in move.paths_to_be_paved:
            self.board.set_path(curr_player, path, Road.Unpaved)
            curr_player.add_resources_for_road()
        for loc1 in move.locations_to_be_set_to_settlements:
            self.board.set_location(curr_player, loc1, Colony.Uncolonised)
            curr_player.add_resources_for_settlement()
        for loc2 in move.locations_to_be_set_to_cities:
            self.board.set_location(curr_player, loc2, Colony.Uncolonised)
            curr_player.add_resources_for_city()
        for count in range(0, move.development_cards_to_be_purchased_count):
            # TODO add purchase card mechanism here. should apply : curr_player.add_unexposed_development_card(zzzzzz)
            curr_player.add_resources_for_development_card()


class CatanMove(AbstractMove):
    def __init__(self):
        # TODO add resource exchange mechanism
        self.development_cards_to_be_exposed = []
        self.paths_to_be_paved = []
        self.locations_to_be_set_to_settlements = []
        self.locations_to_be_set_to_cities = []
        self.development_cards_to_be_purchased_count = 0
