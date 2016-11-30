from typing import Dict

from algorithms.abstract_state import AbstractState, AbstractMove
from algorithms.monte_carlo import MonteCarlo
from game.resource import Resource
from players.abstract_player import AbstractPlayer
from players.random_player import RandomPlayer


class MonteCarloPlayer(AbstractPlayer):
    def __init__(self, seed=None, timeout_seconds=5):
        assert seed is None or (isinstance(seed, int) and seed > 0)

        super().__init__(seed, timeout_seconds)
        self._monte_carlo = MonteCarlo(seed, timeout_seconds)

    def choose_move(self, state: AbstractState) -> AbstractMove:
        self._monte_carlo.start_turn_timer()
        return self._monte_carlo.get_best_move(state)

    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        # TODO implement
        # for the meantime use the random choice of RandomPlayer
        # kind of a hack. but how awesome is that?!
        return RandomPlayer.choose_resources_to_drop(self)
