from itertools import chain

import networkx
import enum
import random
from typing import List, Tuple
from collections import OrderedDict, namedtuple

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


class Resource(enum.Enum):
    Brick = 1
    Lumber = 2
    Wool = 3
    Grain = 4
    Ore = 5
    Desert = 6


class Colony(enum.Enum):
    Settlement = 1
    City = 2
    Empty = 3


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
    _vertices_rows = [
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
    _vertices = [v for vertices_row in _vertices_rows for v in vertices_row]

    def __init__(self):
        self._shuffle_map()
        self._create_graph()

    def get_all_settleable_locations(self) -> List[Vertex]:
        """get non-colonised (empty vertices) locations on map"""
        return [v for v in self._roads_and_settlements.nodes()
                if self._roads_and_settlements[v]['player'][0] is None]

    def get_settleable_locations_by_player(self, player) -> List[Vertex]:
        """get non-colonised (empty vertices) locations on map that this player can settle"""
        settlements = self.get_settled_locations_by_player(player)
        settleable_locations = []
        for u in settlements:
            one_hop = [v for v in self._roads_and_settlements.neighbors(u)
                       if self._roads_and_settlements[u][v]['player'][0] == player]

            two_hop = [w for v in one_hop for w in self._roads_and_settlements.neighbors(v)
                       if w != u and self._roads_and_settlements[v][w]['player'][0] == player
                       and self._roads_and_settlements.node[w]['player'][0] is None]
            settleable_locations.extend(two_hop)
        return settleable_locations

    def get_unpaved_roads_near_player(self, player) -> List[Edge]:
        """get unpaved (empty edges) roads on map that this player can pave"""
        roads = [e for e in self._roads_and_settlements.edges_iter()
                 if self._roads_and_settlements[e[0]][e[1]]['player'][0] == player]
        locations_non_colonised_by_other_players =\
            [v for v in list(chain(roads))
             if self._roads_and_settlements.node[v]['player'][0] not in [player, None]]
        return [(u, v) for u in locations_non_colonised_by_other_players
                for v in self._roads_and_settlements.neighbors(u)
                if self._roads_and_settlements[u][v]['player'][0] is None]

    def get_settled_locations_by_player(self, player):
        return [v for v in self._roads_and_settlements.nodes()
                if self._roads_and_settlements[v]['player'][0] == player]

    def settle_settlement(self, location, player, colony: Colony):
        self._roads_and_settlements.node[location]['player'] = (player, colony)

    def _shuffle_map(self):
        land_numbers = [2, 12] + [i for i in range(3, 12) if i != 7] * 2
        land_resources = [Resource.Lumber, Resource.Wool, Resource.Grain] * 4 + \
                         [Resource.Brick, Resource.Ore] * 3

        random.shuffle(land_numbers)
        random.shuffle(land_resources)

        land_resources.append(Resource.Desert)
        land_numbers.append(0)

        lands = zip(land_resources, land_numbers, range(len(land_resources)))
        self._lands = [land for land in lands]

    def _create_graph(self):
        edges = Board._create_edges(Board._vertices_rows)

        self._roads_and_settlements = networkx.Graph()
        self._roads_and_settlements.add_nodes_from(Board._vertices)
        self._roads_and_settlements.add_edges_from(edges)

        vertices_map = {vertex: (None, Colony.Empty) for vertex in Board._vertices}
        networkx.set_node_attributes(self._roads_and_settlements, 'player', vertices_map)

        self._link_lands_to_graph()

    @staticmethod
    def _create_edges(vertices_rows):
        edges = []
        for i in range(5):
            Board._create_row_edges(edges, i, i + 1, vertices_rows, i % 2 == 0)
            Board._create_row_edges(edges, -i - 1, -i - 2, vertices_rows, i % 2 == 0)
        Board._create_odd_rows_edges(edges, vertices_rows[5], vertices_rows[6])
        return edges

    @staticmethod
    def _create_row_edges(edges, i, j, vertices_rows, is_even_row):
        if is_even_row:
            Board._create_even_rows_edges(edges, vertices_rows[j], vertices_rows[i])
        else:
            Board._create_odd_rows_edges(edges, vertices_rows[j], vertices_rows[i])

    @staticmethod
    def _create_odd_rows_edges(edges, first_row, second_row):
        for edge in zip(second_row, first_row):
            edges.append(edge)

    @staticmethod
    def _create_even_rows_edges(edges, larger_row, smaller_row):
        for i in range(len(smaller_row)):
            edges.append((smaller_row[i], larger_row[i]))
            edges.append((smaller_row[i], larger_row[i + 1]))

    def _link_lands_to_graph(self):
        vertices_map = self._create_vertices_to_lands_mapping()
        networkx.set_node_attributes(self._roads_and_settlements, 'lands', vertices_map)

        for edge in self._roads_and_settlements.edges_iter():
            lands_intersection = [
                land for land in vertices_map[edge[0]] if land in vertices_map[edge[1]]]
            self._roads_and_settlements[edge[0]][edge[1]]['lands'] = lands_intersection

    def _create_vertices_to_lands_mapping(self):
        land_rows = [
            self._lands[0:3],
            self._lands[3:7],
            self._lands[7:12],
            self._lands[12:16],
            self._lands[16:19]
        ]
        vertices_rows_per_land_row = [
            Board._vertices_rows[0:3] + [Board._vertices_rows[3][1:-1]],
            Board._vertices_rows[2:5] + [Board._vertices_rows[5][1:-1]],
            Board._vertices_rows[4:8],
            [Board._vertices_rows[6][1:-1]] + Board._vertices_rows[7:10],
            [Board._vertices_rows[8][1:-1]] + Board._vertices_rows[9:12]
        ]
        vertices_map = {vertex: [] for vertex in Board._vertices}
        for vertices_rows, land_row in zip(vertices_rows_per_land_row, land_rows):
            Board._top_vertex_mapping(vertices_map, vertices_rows[0], land_row)
            Board._middle_vertex_mapping(vertices_map, vertices_rows[1], land_row)
            Board._middle_vertex_mapping(vertices_map, vertices_rows[2], land_row)
            Board._top_vertex_mapping(vertices_map, vertices_rows[3], land_row)
        return vertices_map

    @staticmethod
    def _top_vertex_mapping(vertices_map, vertices, lands):
        for vertex, land in zip(vertices, lands):
            vertices_map[vertex].append(land)

    @staticmethod
    def _middle_vertex_mapping(vertices_map, vertices, lands):
        vertices_map[vertices[0]].append(lands[0])
        vertices_map[vertices[-1]].append(lands[-1])

        for i in range(1, len(vertices[1:-1]) + 1):
            vertices_map[vertices[i]].append(lands[i - 1])
            vertices_map[vertices[i]].append(lands[i])
