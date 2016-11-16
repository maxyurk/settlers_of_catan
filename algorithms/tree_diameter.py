import networkx
from algorithms.dfs import dfs


def tree_diameter(t: networkx.Graph):
    if __debug__:
        assert networkx.is_tree(t)
    v, _ = dfs(t)
    _, longest_path_length = dfs(t, v)
    return longest_path_length
