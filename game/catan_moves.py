from collections import defaultdict

from algorithms.abstract_state import AbstractMove
from players.abstract_player import AbstractPlayer


class CatanMove(AbstractMove):
    def __init__(self, robber_placement_land=None):
        self.resources_exchanges = []
        self.development_cards_to_be_exposed = defaultdict(int)
        self.paths_to_be_paved = []
        self.locations_to_be_set_to_settlements = []
        self.locations_to_be_set_to_cities = []
        self.development_cards_to_be_purchased_count = 0
        self.did_get_largest_army_card = False
        self.did_get_longest_road_card = False
        self.robber_placement_land = robber_placement_land
        self.monopoly_card = None
        self.resources_updates = {}

    def is_doing_anything(self):
        """
        indicate whether anything is done in this move
        :return: True if anything is done in this move, False otherwise
        """
        return (len(self.resources_exchanges) != 0 or
                sum(self.development_cards_to_be_exposed.values()) != 0 or
                len(self.paths_to_be_paved) != 0 or
                len(self.locations_to_be_set_to_settlements) != 0 or
                len(self.locations_to_be_set_to_cities) != 0 or
                self.development_cards_to_be_purchased_count != 0)

    def apply(self, state):
        """
        apply the move in the given state
        :param state: the state to apply the moves on
        :return: None
        """

        # this does almost everything, the rest is done in this method
        state.pretend_to_make_a_move(self)

    def revert(self, state):
        """
        revert the move in the given state
        :param state: the state to revert the moves on
        :return: None
        """

        # this does almost everything, the rest is done in this method
        state.revert_pretend_to_make_a_move(self)


class RandomMove(AbstractMove):
    def __init__(self, rolled_dice: int, state):
        self._rolled_dice = rolled_dice
        self._state = state
        self._previous_rolled_dice = self._state.current_dice_number
        self._resources_by_players = {}

    def apply(self):
        if self._state.is_initialization_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.remove_resource
            self._resources_by_players = {player: player.choose_resources_to_drop() for player in self._state.players}
        else:
            update_method = AbstractPlayer.add_resource
            self._resources_by_players = self._state.board.get_players_to_resources_by_dice_value(self._rolled_dice)
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._rolled_dice

    def revert(self):
        if self._state.is_initialization_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.add_resource
        else:
            update_method = AbstractPlayer.remove_resource
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._previous_rolled_dice