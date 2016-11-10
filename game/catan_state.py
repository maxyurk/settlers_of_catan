from typing import List
from game.board import Board
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
        pass

    def unmake_move(self, move: AbstractMove):
        """reverts specified move"""
        pass

    def get_current_player(self):
        """returns the player that should play next"""
        return self.players[self.current_player_index]
        pass

    def throw_dice(self):
        """throws the dice, and gives players the cards they need"""
        pass
