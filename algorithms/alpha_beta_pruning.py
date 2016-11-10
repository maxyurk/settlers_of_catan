import math
from typing import Callable

from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer


def alpha_beta(state: AbstractState, depth: int, alpha: int, beta: int,
               is_maximizing_player: Callable[[AbstractPlayer], bool],
               evaluate_heuristic_value: Callable[[AbstractState], int]):
    """
    minimax with alpha-beta pruning
    INITIALISATION:
        alpha_beta(current_state, my_max_depth, -Math.inf, Math.inf,
        lambda player: player == self, # or other way to identify maximizing player
        my_heuristic_function)
    :param state: the Game, an interface with necessary methods (see AbstractState for details)
    :param depth: the current depth in the game tree
    :param alpha: the limit from above to the best move
    :param beta: the limit from below to the best move
    :param is_maximizing_player: a function that returns True if specified
    player is the maximizing player, False otherwise
    It should be something like:
        lambda player: player == self
    :param evaluate_heuristic_value: a function that returns a number to
    heuristically evaluate the current state
    :return: best move
    """
    """
    node would be the current state
    get children should return all the possible states after a legal game move
    node is terminal if in the current state someone won
    heuristic value of  a winning (loosing) state is (-)infinity.
    """

    if depth == 0 or state.is_final():
        return evaluate_heuristic_value(state)

    if is_maximizing_player(state.get_current_player()):
        v = -math.inf
        for move in state.get_next_moves():
            state.make_move(move)
            v = max(v, alpha_beta(state, depth - 1, alpha, beta, False))
            state.unmake_move(move)

            alpha = max(v, alpha)
            if beta < alpha:
                break
        return v
    else:
        v = math.inf
        for move in state.get_next_moves():
            state.make_move(move)
            v = min(v, alpha_beta(state, depth - 1, alpha, beta, True))
            state.unmake_move(move)

            beta = min(v, beta)
            if beta < alpha:
                break
        return v
