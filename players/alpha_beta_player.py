from typing import Dict
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax
from game.board import Resource
from game.catan_state import CatanState
from players.random_player import RandomPlayer
from train_and_test.logger import logger


class AlphaBetaPlayer(AbstractPlayer):
    def __init__(self, seed=None, timeout_seconds=5):
        assert seed is None or (isinstance(seed, int) and seed > 0)

        super().__init__(seed, timeout_seconds)
        self.expectimax_alpha_beta = AlphaBetaExpectimax(
            is_maximizing_player=lambda p: p is self,
            evaluate_heuristic_value=lambda s: s.get_scores_by_player()[self],
            timeout_seconds=timeout_seconds)

    def choose_move(self, state: CatanState):
        self.expectimax_alpha_beta.start_turn_timer()
        best_move, move, depth = None, None, 1
        while not self.expectimax_alpha_beta.ran_out_of_time:
            best_move = move
            logger.info('starting depth {}'.format(depth))
            move = self.expectimax_alpha_beta.get_best_move(state, max_depth=depth)
            depth += 1
        if best_move is not None:
            return best_move
        else:
            logger.warning('did not finish depth 1, returning a random move')
            return RandomPlayer.choose_move(self, state)

    def choose_resources_to_drop(self) -> Dict[Resource, int]:
        # TODO implement
        # for the meantime use the random choice of RandomPlayer
        # kind of a hack. but how awesome is that?!
        return RandomPlayer.choose_resources_to_drop(self)
