from unittest import TestCase
from algorithms.abstract_state import AbstractState
from game.abstract_player import AbstractPlayer
from game.catan_state import CatanState
from game.board import *


class FakePlayer(AbstractPlayer):
    def __init__(self, identifier):
        super().__init__()
        self.id = identifier

    def choose_move(self, state: AbstractState):
        pass


class TestCatanState(TestCase):
    def setUp(self):
        super().setUp()
        self.players = [FakePlayer(i) for i in range(2)]
        self.state = CatanState(self.players)

    def test_is_final(self):
        self.assertFalse(self.state.is_final())

        for i in range(21, 26):
            self.state.board.set_location(self.players[0], i, Colony.City)

        self.assertTrue(self.state.is_final())

    def test_get_next_moves(self):
        self.fail()

    def test_make_move(self):
        self.fail()

    def test_unmake_move(self):
        self.fail()

    def test_get_current_player(self):
        self.fail()

    def test_throw_dice(self):
        self.fail()
