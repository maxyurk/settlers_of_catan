from numpy import random

from game.catan_state import CatanState


def create_monte_carlo_filter(seed, branching_factor=3459):
    # noinspection PyUnusedLocal
    def monte_carlo_filter(all_moves, state=None):  # state here to return correct method type
        if len(all_moves) <= branching_factor:
            return all_moves
        return random.RandomState(seed).choice(all_moves, branching_factor, False)

    return monte_carlo_filter


def create_bad_robber_placement_filter(player):
    def is_good_move(move, state) -> bool:
        from game.catan_moves import CatanMove
        assert isinstance(move, CatanMove)
        assert isinstance(state, CatanState)
        if move.robber_placement_land == state.board.get_robber_land():
            return True
        for location in move.robber_placement_land.locations:
            if state.board.is_colonised_by(player, location):
                return False
        return True

    def bad_robber_placement_filter(all_moves, state):
        assert state is not None
        good_moves = [move for move in all_moves if is_good_move(move, state)]
        if not good_moves:
            return all_moves
        return good_moves

    return bad_robber_placement_filter


def create_bad_robber_placement_and_monte_carlo_filter(seed, player, branching_factor=3459):
    a = create_bad_robber_placement_filter(player)
    b = create_monte_carlo_filter(seed, branching_factor)

    def bad_robber_placement_and_monte_carlo_filter(all_moves, state):
        return b(a(all_moves, state), state)

    return bad_robber_placement_and_monte_carlo_filter
