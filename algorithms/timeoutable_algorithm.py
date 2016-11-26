import abc
import signal


class TimeoutableAlgorithm(abc.ABC):
    def __init__(self, timeout_seconds):
        self._timeout_seconds = timeout_seconds
        self.ran_out_of_time = False

    def start_turn_timer(self):
        """
        NOTE: this is NOT implemented to be used in parallel. each time this method is invoked, the signal-handler is
        updated to time-out "self". Which means that if this method is invoked from two different objects,
        only the second player's "ran_out_of_time" flag will be raised
        the algorithm should check at each iteration whether flag self.ran_out_of_time was raised. if it was,
        it should unwind the stack. this is implemented this way in order for the algorithm to be able to revert
        everything it did to the game board.
        So the first lines in the algorithm method should be:
        if self.ran_out_of_time:
            return <something>
        the player should use the algorithm iteratively, knowing his time is limited. for example:
        my_algorithm.start_turn_timer()
        move, best_move = None, None
        while not my_algorithm.ran_out_of_time:
            best_move = move
            move = my_algorithm.get_best_move(state)
        return best_move
        :return: None
        """
        self.ran_out_of_time = False

        def signal_handler(signum, frame):
            self.ran_out_of_time = True
            signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, signal_handler)
        signal.setitimer(signal.ITIMER_REAL, float(self._timeout_seconds))
