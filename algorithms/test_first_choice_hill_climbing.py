from unittest import TestCase

from algorithms.first_choice_hill_climbing import AbstractHillClimbableSpace, first_choice_hill_climbing


class FakeHillClimbableSpace(AbstractHillClimbableSpace):
    def __init__(self):
        self.iterations_count = 0

    def enough_iterations(self) -> bool:
        self.iterations_count += 1
        return self.iterations_count >= 10

    def get_neighbors(self, state: int):
        for i in range(1, 4):
            yield i + state

    def evaluate_state(self, state: int) -> int:
        if state == 2:
            return 10000
        return state

    def is_better(self, first: int, second: int) -> bool:
        return first > second


class TestFirstChoiceHillClimbing(TestCase):
    def test_first_choice_hill_climbing_returns_best_found(self):
        result = first_choice_hill_climbing(FakeHillClimbableSpace(), 1)
        self.assertEqual(result, 2)

    def test_first_choice_hill_climbing_stops_eventually(self):
        first_choice_hill_climbing(FakeHillClimbableSpace(), 4)
        # test fails if it never stopped
