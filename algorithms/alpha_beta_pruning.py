import math
from typing import Callable

from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer


def heuristic_value(state: AbstractState):
    """evaluates the heuristic value of the current state
    Returns:
        Number: evaluated value of current state
    """
    pass


def alpha_beta(state: AbstractState, depth: int, alpha: int, beta: int,
               is_maximizing_player: Callable[[AbstractPlayer], bool]):
    """
    minimax with alpha-beta pruning
    :param state: the Game, an interface with necessary methods (see AbstractState for details)
    :param depth: the current depth in the game tree
    :param alpha: the limit from above to the best move
    :param beta: the limit from below to the best move
    :param is_maximizing_player: a function that returns True if specified
    player is the maximizing player, False otherwise
    It should be something like:
        lambda player: player == self
    :return: best move
    """
    """
    node would be the current state
    get children should return all the possible states after a legal game move
    node is terminal if in the current state someone won
    heuristic value of  a winning (loosing) state is (-)infinity.
    """

    if depth == 0 or state.is_final():
        return heuristic_value(state)

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

# INIT:
# alphabeta(root_node, max_depth, -infinity, infinity, TRUE)
