from typing import List

from algorithms import abstract_state
from game import abstract_player

class CatanState(abstract_state):
    def __init__(self, players: List[abstract_player]):
        self.players = players
        self.current_player_index = 0
        pass

    def is_final(self):
        """
        Returns:
            bool: indicating whether the current state is a final one
        """
        # TODO count points. true if somone has more than 10
        pass

    def get_next_moves(self):
        """computes the next moves available from the current state
        Returns:
            List of AbstractMove: a list of the next moves
        """
        yield None

    def make_move(self, move: abstract_state.AbstractMove):
        """makes specified move"""
        #TODO don't forget to go to next player. somthing like current_player_index = current_player_index+1%len of list
        pass

    def unmake_move(self, move: abstract_state.AbstractMove):
        """reverts specified move"""
        pass

    def get_current_player(self):
        """returns the player that should play next"""
        return self.players[self.current_player_index]
        pass

    def throw_dice(self):
        """throws the dice, and gives players the cards they need"""
        pass
