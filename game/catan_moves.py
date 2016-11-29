from collections import defaultdict
from typing import Dict

from algorithms.abstract_state import AbstractMove, AbstractRandomMove
from game.development_cards import DevelopmentCard
from players.abstract_player import AbstractPlayer


class CatanMove(AbstractMove):
    def __init__(self, robber_placement_land):
        assert robber_placement_land is not None
        self.resources_exchanges = []
        self.development_card_to_be_exposed = None
        self.paths_to_be_paved = {}
        self.locations_to_be_set_to_settlements = []
        self.locations_to_be_set_to_cities = []
        self.development_cards_to_be_purchased_count = 0
        self.did_get_largest_army_card = False
        self.did_get_longest_road_card = False
        self.robber_placement_land = robber_placement_land
        self.monopoly_card = None
        self.monopoly_card_debt = {}
        self.resources_updates = {}

    def is_doing_anything(self):
        """
        indicate whether anything is done in this move
        :return: True if anything is done in this move, False otherwise
        """
        return (len(self.resources_exchanges) != 0 or
                self.development_card_to_be_exposed is not None or
                len(self.paths_to_be_paved) != 0 or
                len(self.locations_to_be_set_to_settlements) != 0 or
                len(self.locations_to_be_set_to_cities) != 0 or
                self.development_cards_to_be_purchased_count != 0)


class RandomMove(AbstractRandomMove):
    @property
    def probability(self):
        return self._probability

    def __init__(self, rolled_dice: int, probability: float, state,
                 development_card_purchases: Dict[DevelopmentCard, int]=defaultdict(int)):
        assert isinstance(probability, float) and 0 <= probability <= 1
        assert rolled_dice in state.probabilities_by_dice_values.keys()

        self._rolled_dice = rolled_dice
        self._development_card_purchases = development_card_purchases
        self._probability = probability
        self._state = state
        self._previous_rolled_dice = self._state.current_dice_number
        self._resources_by_players = {}

    def apply(self):
        if self._state.is_initialisation_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.remove_resource
            self._resources_by_players = {player: player.choose_resources_to_drop() for player in self._state.players}
        else:
            update_method = AbstractPlayer.add_resource
            self._resources_by_players = self._state.board.get_players_to_resources_by_dice_value(self._rolled_dice)
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._rolled_dice

        player = self._state.get_current_player()
        for card, amount in self._development_card_purchases.items():
            for _ in range(amount):
                player.add_unexposed_development_card(card)

    def revert(self):
        if self._state.is_initialisation_phase():
            return
        if self._rolled_dice == 7:
            update_method = AbstractPlayer.add_resource
        else:
            update_method = AbstractPlayer.remove_resource
        AbstractPlayer.update_players_resources(self._resources_by_players, update_method)
        self._state.current_dice_number = self._previous_rolled_dice

        player = self._state.get_current_player()
        for card, amount in self._development_card_purchases.items():
            for _ in range(amount):
                player.remove_unexposed_development_card(card)
