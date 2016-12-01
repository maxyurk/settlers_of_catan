from abc import ABC, abstractmethod
from typing import Iterable, Any

AbstractHillClimbingState = Any

AbstractHillClimbingStateEvaluation = Any


class AbstractHillClimbableSpace(ABC):

    @abstractmethod
    def get_neighbors(self, state: AbstractHillClimbingState) -> Iterable[AbstractHillClimbingState]:
        """
        get an iterable of neighbors of current state
        :param state: current state
        :return: generator of neighbors
        """
        raise NotImplementedError()

    @abstractmethod
    def evaluate_state(self, state: AbstractHillClimbingState) -> AbstractHillClimbingStateEvaluation:
        """
        return someththat evaluates the given state. this is used to compare this state to others
        :param state: state to evaluate
        :return: float representing a "score" of given state, to be compared to others
        """
        raise NotImplementedError()

    @abstractmethod
    def enough_iterations(self) -> bool:
        """
        :return: should stop iterating or not
        """
        raise NotImplementedError()

    @abstractmethod
    def is_better(self, first: AbstractHillClimbingStateEvaluation, second: AbstractHillClimbingStateEvaluation) -> bool:
        """
        :param first: first evaluation
        :param second: second evaluation
        :return: True if first is better than second, False otherwise
        """
        raise NotImplementedError()


def first_choice_hill_climbing(space: AbstractHillClimbableSpace, initial_state: AbstractHillClimbingState)\
        -> AbstractHillClimbingState:
    """
    get approximately best state in given space
    :param space: the space on which to find approximately best state
    :param initial_state: the state to begin the search from
    :return: the best state found given the iterations limit in the space.enough_iterations method
    """
    best_state = initial_state
    best_evaluation = space.evaluate_state(best_state)

    while True:
        previous_best_state = best_state

        for neighbor_state in space.get_neighbors(best_state):
            neighbor_evaluation = space.evaluate_state(neighbor_state)

            if space.is_better(neighbor_evaluation, best_evaluation):
                best_evaluation = neighbor_evaluation
                best_state = neighbor_state

                if space.enough_iterations():
                    return best_state
                break

            if space.enough_iterations():
                return best_state

        if previous_best_state is best_state:
            break

    return best_state

