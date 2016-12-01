import enum


@enum.unique
class Resource(enum.Enum):
    Brick = 0
    Lumber = 1
    Wool = 2
    Grain = 3
    Ore = 4


LastResourceIndex = 4  # must be the same as the last resource
FirsResourceIndex = 0  # must be the same as the first resource


class ResourceAmounts(dict):
    road = {
        Resource.Brick: 1,
        Resource.Lumber: 1,
        Resource.Wool: 0,
        Resource.Grain: 0,
        Resource.Ore: 0,
    }

    settlement = {
        Resource.Brick: 1,
        Resource.Lumber: 1,
        Resource.Wool: 1,
        Resource.Grain: 1,
        Resource.Ore: 0
    }

    city = {
        Resource.Brick: 0,
        Resource.Lumber: 0,
        Resource.Wool: 0,
        Resource.Grain: 2,
        Resource.Ore: 3
    }

    development_card = {
        Resource.Brick: 0,
        Resource.Lumber: 0,
        Resource.Wool: 1,
        Resource.Grain: 1,
        Resource.Ore: 1,
    }

    def __init__(self):
        super().__init__({resource: 0 for resource in Resource})

    def _add(self, resources_amount):
        for resource, amount in resources_amount.items():
            self[resource] += amount

    def add_road(self):
        self._add(ResourceAmounts.road)
        return self

    def add_settlement(self):
        self._add(ResourceAmounts.settlement)
        return self

    def add_city(self):
        self._add(ResourceAmounts.city)
        return self

    def add_development_card(self):
        self._add(ResourceAmounts.development_card)
        return self
