from typing import Dict
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax
from game.board import Resource
from game.catan_state import CatanState
from players.random_player import RandomPlayer


class AlphaBetaPlayer(AbstractPlayer):
    def __init__(self, max_depth: int = 5, seed=None):
        super().__init__(seed)
        self.expectimax_alpha_beta = AlphaBetaExpectimax(
            None, max_depth, lambda p: p == self, lambda s: s.get_scores_by_player()[self])

    def choose_move(self, state: CatanState):
        self.expectimax_alpha_beta.state = state
        return self.expectimax_alpha_beta.get_best_move()

    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        # TODO implement
        # for the meantime use the random choice of RandomPlayer
        # kind of a hack. but how awesome is that?!
        return RandomPlayer.choose_resources_to_drop(self)
