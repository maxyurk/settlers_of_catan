import abc
import math


class AbstractMove(abc.ABC):
    pass


class AbstractState(abc.ABC):

    @abc.abstractmethod
    def is_final(self):
        """
        Returns:
            bool: indicating whether the current state is a final one
        """
        pass

    @abc.abstractmethod
    def heuristic_value(self):
        """evaluates the heuristic value of the current state
        Returns:
            Number: evaluated value of current state
        """
        pass

    @abc.abstractmethod
    def get_next_moves(self):
        """computes the next moves available from the current state
        Returns:
            List of AbstractMove: a list of the next moves
        """
        yield None

    @abc.abstractmethod
    def make_move(self, move: AbstractMove):
        """makes specified move"""
        pass

    @abc.abstractmethod
    def unmake_move(self, move: AbstractMove):
        """reverts specified move"""
        pass


def alpha_beta(state: AbstractState, depth, alpha, beta, is_maximizing_player):
    """
    node would be the current state
    get children should return all the possible states after a legal game move
    node is terminal if in the current state someone won
    huristic value of  a winning (loosing) state is (-)infinity.
    """

    if depth == 0 or state.is_final():
        return state.heuristic_value()

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
