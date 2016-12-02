import os

from game.catan_state import CatanState
from players.alpha_beta_player import AlphaBetaPlayer
from players.alpha_beta_weighted_probabilities_player import AlphaBetaWeightedProbabilitiesPlayer
from train_and_test.logger import logger, fileLogger


def scores_changed(state, previous_scores, scores):
    for player in state.players:
        if previous_scores[player] != scores[player]:
            return True
    return False


def clean_previous_images():
    for file_name in os.listdir(path='.'):
        if file_name.split(sep='_')[0] == 'turn':
            os.remove(file_name)


def execute_game(seed):

    timeout_seconds = 5
    p0 = AlphaBetaWeightedProbabilitiesPlayer(seed, timeout_seconds)
    p1 = AlphaBetaPlayer(seed, timeout_seconds)
    p2 = AlphaBetaPlayer(seed, timeout_seconds)
    p3 = AlphaBetaPlayer(seed, timeout_seconds)
    players = [p0, p1, p2, p3]

    state = CatanState(players, seed)

    turn_count = 0
    score_by_player = state.get_scores_by_player()
    # state.board.plot_map('turn_{}_scores_{}.png'
    #                      .format(turn_count, ''.join('{}_'.format(v) for v in score_by_player.values())))

    while not state.is_final():
        # noinspection PyProtectedMember
        logger.info('----------------------p{}\'s turn----------------------'.format(state._current_player_index))

        turn_count += 1
        robber_placement = state.board.get_robber_land()

        move = state.get_current_player().choose_move(state)
        assert not scores_changed(state, score_by_player, state.get_scores_by_player())
        state.make_move(move)
        state.make_random_move()

        previous_score_by_player = score_by_player
        score_by_player = state.get_scores_by_player()

        if scores_changed(state, previous_score_by_player, score_by_player):
            scores = ''.join('{} '.format(v) for v in score_by_player.values())
            move_data = {k: v for k, v in move.__dict__.items() if v and k != 'resources_updates' and not
                         (k == 'robber_placement_land' and v == robber_placement) and not
                         (isinstance(v, dict) and sum(v.values()) == 0)}
            logger.info('| {}| turn: {:3} | move:{} |'.format(scores, turn_count, move_data))

            # image_name = 'turn_{}_scores_{}.png'.format(
            #     turn_count, ''.join('{}_'.format(v) for v in score_by_player.values()))
            # state.board.plot_map(image_name, state.current_dice_number)

    players_scores_by_names = {
        (k, v.__class__, v.expectimax_alpha_beta.evaluate_heuristic_value.__name__
         if isinstance(v, AlphaBetaPlayer) else None): score_by_player[v]
        for k, v in locals().items() if v in players
        }
    fileLogger.info('\n' + '\n'.join(' {:150} : {} '.format(str(name), score)
                                     for name, score in players_scores_by_names.items()) +
                    '\n turns it took: {}\n'.format(turn_count) + ('-' * 156))


def main():
    for seed in range(1, 4):
        clean_previous_images()
        execute_game(seed)

if __name__ == '__main__':
    main()
