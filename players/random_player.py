import random
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from train_and_test import logger


class RandomPlayer(AbstractPlayer):

    def __init__(self, seed=None):
        super().__init__(seed)

    def choose_move(self, state: AbstractState):
        return self._random_choice(state.get_next_moves())
