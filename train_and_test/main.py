from game.catan_state import CatanState
from game.pieces import Colony, Road
from players.alpha_beta_player import *
from players.random_player import *

if __name__ == '__main__':
    p1 = AlphaBetaPlayer(1)
    p2 = AlphaBetaPlayer(1)
    # p1 = RandomPlayer()
    # p2 = RandomPlayer()
    state = CatanState([p1, p2])

    state._board.set_location(p1, 0, Colony.Settlement)
    state._board.set_location(p1, 1, Colony.Settlement)
    state._board.set_location(p1, 14, Colony.Settlement)
    state._board.set_location(p1, 23, Colony.Settlement)

    state._board.set_path(p1, (0, 4), Road.Paved)
    state._board.set_path(p1, (4, 1), Road.Paved)
    state._board.set_path(p1, (14, 9), Road.Paved)
    state._board.set_path(p1, (23, 17), Road.Paved)

    state._board.set_location(p2, 52, Colony.Settlement)
    state._board.set_location(p2, 53, Colony.Settlement)
    state._board.set_location(p2, 22, Colony.Settlement)
    state._board.set_location(p2, 36, Colony.Settlement)

    state._board.set_path(p2, (52, 49), Road.Paved)
    state._board.set_path(p2, (49, 53), Road.Paved)
    state._board.set_path(p2, (22, 28), Road.Paved)
    state._board.set_path(p2, (36, 31), Road.Paved)

    c = 0
    previous_scores = state.get_scores_by_player()
    while not state.is_final():
        c += 1

        state.throw_dice()
        state.make_move(state.get_current_player().choose_move(state))

        scores = state.get_scores_by_player()
        for player in state._players:
            if previous_scores[player] != scores[player]:
                previous_scores = scores
                print('\n{}:{} | turn: {}'.format(scores[p1], scores[p2], c), flush=True)
            else:
                print('.', sep='', end='', flush=True)
    print('\n{}:{} | turn: {}'.format(scores[p1], scores[p2], c), flush=True)