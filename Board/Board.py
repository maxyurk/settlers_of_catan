import numpy

"""
The board is represented as follows:
This map (W2 means wheat with the number 5 on it, M2 is metal with 2 on it):

    O     O
 /    \ /    \
O      O      O
| (W5) | (M2) |
O      O      O
 \    / \    /
    O     O

In the DS (which is just a 2D numpy array), will be represented as follows:

 --- --- --- --- --- --- --- --- ---
| O | - | O | - | O | - | O | - | O |
 --- --- --- --- --- --- --- --- ---
| | |nil| W5|nil| | |nil| M2|nil| | |
 --- --- --- --- --- --- --- --- ---
| O | - | O | - | O | - | O | - | O |
 --- --- --- --- --- --- --- --- ---

 The first line of the array is this part of the map:
    O     O
 /    \ /    \
O      O      O
The second line is:
| (W5) | (M2) |
And the third:
O      O      O
 \    / \    /
    O     O

"""