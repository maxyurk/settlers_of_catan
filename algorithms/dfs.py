import networkx
from collections import deque

stack = deque(maxlen=54)


def dfs(g: networkx.Graph, v: int=None):
    """
    traverses in a depth-first-search manner the graph
    :param g: the graph to traverse (Note: the graph is assumed to have a single component)
    :param v: the node to start traversal from. if not given, the first in g.nodes_iter() is used
    :return: the farthest node in the traversal, and the path length from that
    """
    stack.clear()

    max_height = 0
    furthest_node = None
    if v is None:
        v = next(g.nodes_iter())
    visited = {v}
    stack.append(v)

    while not len(stack) == 0:
        u = stack[-1]

        u_has_unvisited_neighbors = False
        for w in g.neighbors(u):
            if w not in visited:
                visited.add(w)
                stack.append(w)
                u_has_unvisited_neighbors = True
                break

        if len(stack) > max_height:
            max_height = len(stack)
            furthest_node = stack[-1]

        if not u_has_unvisited_neighbors:
            stack.pop()

    return furthest_node, max_height
