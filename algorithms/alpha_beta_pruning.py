import math

from algorithms.abstract_state import AbstractState


def heuristic_value(state: AbstractState):
    """evaluates the heuristic value of the current state
    Returns:
        Number: evaluated value of current state
    """
    pass


def alpha_beta(state: AbstractState, depth, alpha, beta, is_maximizing_player):
    """
    node would be the current state
    get children should return all the possible states after a legal game move
    node is terminal if in the current state someone won
    huristic value of  a winning (loosing) state is (-)infinity.
    """

    if depth == 0 or state.is_final():
        return heuristic_value(state)

    if is_maximizing_player:
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
