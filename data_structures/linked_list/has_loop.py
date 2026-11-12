"""Detect whether a singly linked list contains a loop:
https://en.wikipedia.org/wiki/Cycle_detection#Floyd's_tortoise_and_hare
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class ContainsLoopError(Exception):
    """Exception raised when iterating over a linked list that contains a loop."""


class Node:
    """Singly linked list node."""

    def __init__(self, data: Any) -> None:
        """Initialize node with `data` and `next_node = None`."""
        self.data: Any = data
        self.next_node: Node | None = None

    def __iter__(self) -> Iterator[Any]:
        """Iterate over linked list values, raising `ContainsLoopError` on a cycle."""
        node: Node | None = self
        visited: set[Node] = set()
        while node:
            if node in visited:
                raise ContainsLoopError
            visited.add(node)
            yield node.data
            node = node.next_node

    @property
    def has_loop(self) -> bool:
        """
        A loop is when the exact same Node appears more than once in a linked list.
        >>> root_node = Node(1)
        >>> root_node.next_node = Node(2)
        >>> root_node.next_node.next_node = Node(3)
        >>> root_node.next_node.next_node.next_node = Node(4)
        >>> root_node.has_loop
        False
        >>> root_node.next_node.next_node.next_node = root_node.next_node
        >>> root_node.has_loop
        True
        """
        try:
            list(self)
            return False
        except ContainsLoopError:
            return True


if __name__ == "__main__":
    import doctest

    doctest.testmod()
