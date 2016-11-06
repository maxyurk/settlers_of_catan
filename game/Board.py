import numpy
import networkx
import enum
import random
from typing import List, Tuple


"""
Structure
---------
The board is represented as follows:
It consists of two parts:
a graph that represents the items around the hexagon, and an array of the hexagons.
The graph will hold the "shape":
 -each vertex will be a place a house can be built in
 -each edge will be a place a road can be paved at
THe array will hold the "data":
 -each item will be a hexagon, that consists of:
    --the element (Wheat, Metal, Clay or Wood)
    --the number (2-12)
    --Is there a burglar on the hexagon or not
each edge & vertex in the graph will be bi-directionally linked to it's hexagons, for easy traversal

Example
-------
This map (W2 means wheat with the number 5 on it, M2 is metal with 2 on it):

    O     O
 /    \ /    \
O      O      O
| (W5) | (M2) |
O      O      O
 \    / \    /
    O     O

In the DS, will be represented as follows:
The array:
 ---- ----
| W5 | M2 |
 ---- ----
The graph will have the shape of the map, where the edges are \,/,|
and the vertices are O.
    O     O
 /    \ /    \
O      O      O
|      |      |
O      O      O
 \    / \    /
    O     O

"""


def _create_graph():
    vertices_rows = [
        [i for i in range(0, 3)],
        [i for i in range(3, 7)],
        [i for i in range(7, 11)],
        [i for i in range(11, 16)],
        [i for i in range(16, 21)],
        [i for i in range(21, 27)],
        [i for i in range(27, 33)],
        [i for i in range(33, 38)],
        [i for i in range(38, 43)],
        [i for i in range(43, 47)],
        [i for i in range(47, 51)],
        [i for i in range(51, 54)]
    ]
    vertices = [v for vertices_row in vertices_rows for v in vertices_row]
    edges = _create_edges(vertices_rows)
    g = networkx.Graph()
    g.add_nodes_from(vertices)
    g.add_edges_from(edges)
    return g


def _create_edges(vertices_rows):
    edges = []
    for i in range(5):
        _create_row_edges(edges, i, i + 1, vertices_rows, i % 2 == 0)
        _create_row_edges(edges, -i - 1, -i - 2, vertices_rows, i % 2 == 0)
    _create_odd_rows_edges(edges, vertices_rows[5], vertices_rows[6])
    return edges


def _create_row_edges(edges, i, j, vertices_rows, is_even_row):
    if is_even_row:
        _create_even_rows_edges(edges, vertices_rows[j], vertices_rows[i])
    else:
        _create_odd_rows_edges(edges, vertices_rows[j], vertices_rows[i])


def _create_odd_rows_edges(edges, first_row, second_row):
    for edge in zip(second_row, first_row):
        edges.append(edge)


def _create_even_rows_edges(edges, larger_row, smaller_row):
    for i in range(len(smaller_row)):
        edges.append((smaller_row[i], larger_row[i]))
        edges.append((smaller_row[i], larger_row[i + 1]))


class Resource(enum.Enum):
    Brick = 1
    Lumber = 2
    Wool = 3
    Grain = 4
    Ore = 5
    Desert = 6


class Vertex:
    def __init__(self):
        pass

    def get_surrounding_resources(self) -> List[Tuple[Resource, int]]:
        """get resources surrounding this settlement"""
        pass


class Edge:
    def __init__(self):
        pass


class Board:

    def __init__(self):
        self._shuffle_map()
        self._create_graph()

    def _create_graph(self):
        self._roads_and_villages = _create_graph()

    def _shuffle_map(self):
        _land_numbers = [2, 12] + [i for i in range(3, 11)] * 2
        _land_resources = [Resource.Brick, Resource.Ore] * 3 + \
                          [Resource.Lumber, Resource.Wool, Resource.Grain] * 4

        random.shuffle(_land_numbers)
        random.shuffle(_land_resources)

        _land_resources.append(Resource.Desert)
        _land_numbers.append(0)

        self._lands = zip(_land_resources, _land_numbers)

    def get_all_settleable_locations(self) -> List[Vertex]:
        """get non-colonised (empty vertices) locations on map"""
        pass

    def get_settleable_locations_by_player(self, player) -> List[Vertex]:
        """get non-colonised (empty vertices) locations on map that this player can settle"""
        pass

    def get_unpaved_roads_near_player(self, player) -> List[Edge]:
        """get unpaved (empty edges) roads on map that this player can pave"""
        pass
