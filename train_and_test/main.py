import os

from game.catan_state import CatanState
from players.alpha_beta_player import AlphaBetaPlayer
from players.random_player import RandomPlayer
from train_and_test.logger import logger


def scores_changed(state, previous_scores, scores):
    for player in state.players:
        if previous_scores[player] != scores[player]:
            return True
    return False


def clean_previous_images():
    for file_name in os.listdir(None):
        if file_name.split(sep='_')[0] == 'turn':
            os.remove(file_name)


def execute_game():
    seed = None  # 0.35 - this number, when used with alpha-beta players, produces a very slow game
    timeout_seconds = 1
    p1 = AlphaBetaPlayer(seed, timeout_seconds)
    # p2 = AlphaBetaPlayer(seed, timeout_seconds)
    # p1 = RandomPlayer(seed)
    p2 = RandomPlayer(seed)
    state = CatanState([p1, p2], seed)

    clean_previous_images()

    turn_count = 0
    previous_scores = state.get_scores_by_player()
    logger.info('| p1 {}:p2 {} | turn: {} | game start |'.format(previous_scores[p1], previous_scores[p2], turn_count))
    state.board.plot_map('turn_{}_{}_to_{}.png'.format(turn_count, previous_scores[p1], previous_scores[p2]))
    while not state.is_final():
        logger.info('-----------------{}\'s turn-----------------'
                    .format('p1' if state.get_current_player() is p1 else 'p2'))
        turn_count += 1
        robber_placement = state.board.get_robber_land()

        state.throw_dice()
        # --------------------------------------
        # TODO remove
        if __debug__ and scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.error('~BUG throw dice changed score~')
            exit(1)
        # --------------------------------------
        move = state.get_current_player().choose_move(state)
        # --------------------------------------
        # TODO remove
        if __debug__ and scores_changed(state, previous_scores, state.get_scores_by_player()):
            logger.error('~BUG choose move changed score~')
            exit(1)
        # --------------------------------------
        state.make_move(move)

        current_scores = state.get_scores_by_player()
        score_changed = scores_changed(state, previous_scores, current_scores)
        if score_changed:
            previous_scores = current_scores

        if move.is_doing_anything():
            move_data = {k: v for k, v in move.__dict__.items() if v and k != 'resources_updates' and not
                         (k == 'robber_placement_land' and v == robber_placement)}
            logger.info('| p1 {}:p2 {} | turn: {} | move:{} |'
                        .format(current_scores[p1], current_scores[p2], turn_count, move_data))
            state.board.plot_map('turn_{}_{}_to_{}.png'.format(turn_count, current_scores[p1], current_scores[p2]))
        elif __debug__ and score_changed:
            # TODO remove
            logger.error('~BUG. score changed, without movement | p1 {}:p2 {} | turn: {}'
                         .format(current_scores[p1], current_scores[p2], turn_count))
            exit(1)
        logger.info('-----------------{}\'s done-----------------'
                    .format('p2' if state.get_current_player() is p1 else 'p1'))
    logger.info('| p1 {}:p2 {} | turn: {} | game end |'.format(previous_scores[p1], previous_scores[p2], turn_count))


def main():
    for _ in range(1):
        execute_game()

if __name__ == '__main__':
    main()
