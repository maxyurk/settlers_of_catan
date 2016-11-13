import random
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer


class RandomPlayer(AbstractPlayer):
    def choose_move(self, state: AbstractState):
        return random.choice(state.get_next_moves())
