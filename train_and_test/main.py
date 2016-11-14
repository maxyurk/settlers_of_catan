from game.catan_state import CatanState
from game.pieces import Colony, Road
from players.alpha_beta_player import *
from players.random_player import *

if __name__ == '__main__':
    p1 = AlphaBetaPlayer()
    p2 = RandomPlayer()
    state = CatanState([p1, p2])

    state._board.set_location(p1, 0, Colony.Settlement)
    state._board.set_location(p1, 1, Colony.Settlement)
    state._board.set_path(p1, (0, 4), Road.Paved)
    state._board.set_path(p1, (4, 1), Road.Paved)

    state._board.set_location(p1, 52, Colony.Settlement)
    state._board.set_location(p1, 53, Colony.Settlement)
    state._board.set_path(p1, (52, 49), Road.Paved)
    state._board.set_path(p1, (49, 53), Road.Paved)

    while not state.is_final():
        print('.', sep='', end='', flush=True)
        current_move = state.get_current_player().choose_move(state)
        state.throw_dice()
        state.make_move(current_move)
