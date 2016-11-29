from typing import Dict, Callable, List

from algorithms.abstract_state import AbstractState, AbstractMove
from algorithms.alpha_beta_pruning_expectimax import AlphaBetaExpectimax
from game.board import Resource
from game.catan_state import CatanState
from players.abstract_player import AbstractPlayer
from players.random_player import RandomPlayer
from train_and_test.logger import logger


class AlphaBetaPlayer(AbstractPlayer):
    def __init__(self, seed=None, timeout_seconds=5):
        assert seed is None or (isinstance(seed, int) and seed > 0)

        super().__init__(seed, timeout_seconds)

        def default_heuristic_function(state):
            return float(state.get_scores_by_player()[self])

        self.expectimax_alpha_beta = AlphaBetaExpectimax(
            is_maximizing_player=lambda p: p is self,
            evaluate_heuristic_value=default_heuristic_function,
            timeout_seconds=timeout_seconds)

    def choose_move(self, state: CatanState):
        self.expectimax_alpha_beta.start_turn_timer()
        best_move, move, depth = None, None, 1
        while not self.expectimax_alpha_beta.ran_out_of_time:
            best_move = move
            logger.info('starting depth {}'.format(depth))
            move = self.expectimax_alpha_beta.get_best_move(state, max_depth=depth)
            depth += 2
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

    def set_heuristic(self, evaluate_heuristic_value: Callable[[AbstractState], float]):
        """
        set heuristic evaluation of a state in a game
        :param evaluate_heuristic_value: a callable that given state returns a float. higher means "better" state
        """
        self.expectimax_alpha_beta.evaluate_heuristic_value = evaluate_heuristic_value

    def set_filter(self, filter_moves: Callable[[List[AbstractMove]], List[AbstractMove]]):
        """
        set the filtering of moves in each step
        :param filter_moves: a callable that given list of moves, returns a list of moves that will be further developed
        """
        self.expectimax_alpha_beta.filter_moves = filter_moves