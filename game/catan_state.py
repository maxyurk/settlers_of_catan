import copy
import random
from typing import List, Callable
from game.board import Board, Resource, Road, Colony
from algorithms.abstract_state import AbstractState, AbstractMove
from game.abstract_player import AbstractPlayer


class CatanState(AbstractState):
    def __init__(self, players: List[AbstractPlayer]):
        self.players = players
        self.current_player_index = 0
        self.board = Board()

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
        yield None

    def make_move(self, move: AbstractMove):
        """makes specified move"""
        #TODO don't forget to go to next player. somthing like current_player_index = current_player_index+1%len of list
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




