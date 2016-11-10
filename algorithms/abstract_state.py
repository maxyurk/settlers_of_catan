import abc


class AbstractState(abc.ABC):

    @abc.abstractmethod
    def is_final(self):
        """
        Returns:
            bool: indicating whether the current state is a final one
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

    @abc.abstractmethod
    def get_current_player(self):
        """returns the player that should play next"""
        pass

    @abc.abstractmethod
    def throw_dice(self):
        """throws the dice, and gives players the cards they need"""
        pass


class AbstractMove(abc.ABC):
    pass