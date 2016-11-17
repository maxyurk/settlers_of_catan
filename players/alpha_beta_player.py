from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax
from game.catan_state import CatanState


class AlphaBetaPlayer(AbstractPlayer):
    def __init__(self, max_depth: int = 5, seed=None):
        super().__init__(seed)
        self.expectimax_alpha_beta = AlphaBetaExpectimax(
            None, max_depth, lambda p: p == self, lambda s: s.get_scores_by_player()[self])

    def choose_move(self, state: CatanState):
        self.expectimax_alpha_beta.state = state
        return self.expectimax_alpha_beta.get_best_move()
