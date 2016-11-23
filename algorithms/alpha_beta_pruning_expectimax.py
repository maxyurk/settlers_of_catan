import math
from typing import Callable

from algorithms.abstract_state import AbstractState
from algorithms.timeoutable_algorithm import TimeoutableAlgorithm
from game.abstract_player import AbstractPlayer


class AlphaBetaExpectimax(TimeoutableAlgorithm):
    def __init__(self, is_maximizing_player: Callable[[AbstractPlayer], bool],
                 evaluate_heuristic_value: Callable[[AbstractState], int], timeout_seconds=5):
        """
        wrapper of the expectiamx with alpha-beta pruning algorithm
        it inherits from TimeoutableAlgorithm to enable iterative deepening
        :param is_maximizing_player: a function that returns True if specified
        player is the maximizing player, False otherwise
        It should be something like:
            lambda player: player == self
        :param evaluate_heuristic_value: a function that returns a number to
        heuristically evaluate the current state
        :return: best move
        """
        super().__init__(timeout_seconds)
        self.state = None
        self.max_depth = 0
        self._is_maximizing_player = is_maximizing_player
        self._evaluate_heuristic_value = evaluate_heuristic_value

    def get_best_move(self, state, max_depth):
        """
        get best move, based on the expectimax with alpha-beta pruning algorithm
        with given heuristic function
        :param state: the Game, an interface with necessary methods
        (see AbstractState for details)
        :param max_depth: the maximum depth the algorithm will reach in the game tree
        :return: the best move
        """
        self.state = state
        self.max_depth = max_depth
        assert max_depth > 0
        assert state is not None
        _, best_move = self._alpha_beta_expectimax(self.max_depth, -math.inf, math.inf, False)
        return best_move

    def _alpha_beta_expectimax(self, depth: int, alpha: int, beta: int, is_random_event: bool):
        """
        expectimax with alpha-beta pruning
        INITIALISATION:
            alpha_beta(self.max_depth, -Math.inf, Math.inf, False)
        :param depth: the current depth in the game tree
        :param alpha: the limit from above to the best move
        :param beta: the limit from below to the best move
        :param is_random_event: boolean indicating whether it's a node of random event (dice thrown)
        :return: best move
        """
        if self.ran_out_of_time:
            return 0, None

        if depth == 0 or self.state.is_final():
            return self._evaluate_heuristic_value(self.state), None

        if is_random_event:
            v = 0

            for number, probability in self.state.get_numbers_to_probabilities().items():
                random_move = self.state.throw_dice(number)
                u, _ = self._alpha_beta_expectimax(depth - 1, alpha, beta, False)
                v += probability * u
                self.state.unthrow_dice(random_move)
            return v, None
        elif self._is_maximizing_player(self.state.get_current_player()):
            v = -math.inf
            best_move = None
            for move in self.state.get_next_moves():
                self.state.make_move(move)
                u, _ = self._alpha_beta_expectimax(depth - 1, alpha, beta, True)
                if u > v:
                    v = u
                    best_move = move
                self.state.unmake_move(move)

                alpha = max(v, alpha)
                if beta <= alpha:
                    break
            return v, best_move
        else:
            v = math.inf
            for move in self.state.get_next_moves():
                self.state.make_move(move)
                u, _ = self._alpha_beta_expectimax(depth - 1, alpha, beta, True)
                v = min(v, u)
                self.state.unmake_move(move)

                beta = min(v, beta)
                if beta <= alpha:
                    break
            return v, None
