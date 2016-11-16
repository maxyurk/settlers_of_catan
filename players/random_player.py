import random
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
import numpy as np
from train_and_test import logger


class RandomPlayer(AbstractPlayer):
    c = 10

    def __init__(self, seed=None):
        super().__init__()
        if seed is not None and not (0 <= seed < 1):
            logger.error('{parameter_name} should be in the range [0,1). treated as if no {parameter_name}'
                         ' was sent'.format(parameter_name=RandomPlayer.__init__.__code__.co_varnames[1]))
            seed = None
        RandomPlayer.c += 1
        numpy_seed = None if seed is None else int(seed * RandomPlayer.c)
        self._random_choice = np.random.RandomState(seed=numpy_seed).choice

    def choose_move(self, state: AbstractState):
        return self._random_choice(state.get_next_moves())
