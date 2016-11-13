from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax


class AlphaBetaPlayer(AbstractPlayer):
    def choose_move(self, state: AbstractState):
        return AlphaBetaExpectimax(state, 5, lambda p: p == self, lambda s: 0).get_best_move()
