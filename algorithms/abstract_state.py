import abc
from typing import List


class AbstractMove(abc.ABC):
    pass


class AbstractRandomMove(AbstractMove):
    @property
    def probability(self):
        """
        :return: the probability of this random move to happen
        """
        raise NotImplementedError()


class AbstractState(abc.ABC):

    @abc.abstractmethod
    def is_final(self):
        """
        Returns:
            bool: indicating whether the current state is a final one
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_next_moves(self):
        """
        computes the next moves available from the current state
        :return List of AbstractMove: a list of the next moves
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def make_move(self, move: AbstractMove):
        """makes specified move"""
        raise NotImplementedError()

    @abc.abstractmethod
    def unmake_move(self, move: AbstractMove):
        """reverts specified move"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_current_player(self):
        """returns the player that should play next"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_next_random_moves(self) -> List[AbstractRandomMove]:
        """
        computes the next random moves available from the current state
        :return List of AbstractMove: a list of the next random moves
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def make_random_move(self, move: AbstractRandomMove):
        """makes specified random move"""
        raise NotImplementedError()

    @abc.abstractmethod
    def unmake_random_move(self, move: AbstractRandomMove):
        """reverts specified random move"""
        raise NotImplementedError()
