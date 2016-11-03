infinity = 99999999


# node would be the current state
# nodes must be immutable
# get children should return all the possible states after a legal game move
# (without modifying the current state - nodes are immutable)
# node is terminal if in the current state someone won
# huristic value of  a winning (loosing) state is (-)infinity.

def alpha_beta(node, depth, alpha, beta, is_maximizing_player):
    if depth == 0 or is_terminal(node):
        return heuristic_value(node)
    if is_maximizing_player:
        v = -infinity
        for child in get_children(node):
            v = max(v, alpha_beta(child, depth - 1, alpha, beta, False))
            alpha = max(v, alpha)
            if beta < alpha:
                break
        return v
    else:
        v = infinity
        for child in get_children(node):
            v = min(v, alpha_beta(child, depth - 1, alpha, beta, True))
            beta = min(v, beta)
            if beta < alpha:
                break
        return v

# INIT:
# alphabeta(root_node, max_depth, -infinity, infinity, TRUE)
