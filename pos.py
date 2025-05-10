from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

# --- 外部静态表 ---
_DIRECTION_TO_DELTA = {
    'UP': (-1, 0),
    'DOWN': (1, 0),
    'LEFT': (0, -1),
    'RIGHT': (0, 1),
    'UP_LEFT': (-1, -1),
    'UP_RIGHT': (-1, 1),
    'DOWN_LEFT': (1, -1),
    'DOWN_RIGHT': (1, 1),
}

_DIRECTION_ROTATE_ORDER = [
    'UP_LEFT',
    'UP',
    'UP_RIGHT',
    'RIGHT',
    'DOWN_RIGHT',
    'DOWN',
    'DOWN_LEFT',
    'LEFT'
]

_DIRECTION_OPPOSITE = {
    'UP': 'DOWN',
    'DOWN': 'UP',
    'LEFT': 'RIGHT',
    'RIGHT': 'LEFT',
    'UP_LEFT': 'DOWN_RIGHT',
    'UP_RIGHT': 'DOWN_LEFT',
    'DOWN_LEFT': 'UP_RIGHT',
    'DOWN_RIGHT': 'UP_LEFT',
}

_DIRECTION_DIAGONALS = {
    'UP_LEFT', 'UP_RIGHT', 'DOWN_LEFT', 'DOWN_RIGHT'
}


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    UP_LEFT = auto()
    UP_RIGHT = auto()
    DOWN_LEFT = auto()
    DOWN_RIGHT = auto()

    def to_delta(self) -> Tuple[int, int]:
        return _DIRECTION_TO_DELTA[self.name]

    def rotate(self, step: int = 1) -> "Direction":
        order = _DIRECTION_ROTATE_ORDER
        idx = order.index(self.name)
        new_idx = (idx + step) % 8
        return Direction[_DIRECTION_ROTATE_ORDER[new_idx]]

    def opposite(self) -> "Direction":
        return Direction[_DIRECTION_OPPOSITE[self.name]]

    @staticmethod
    def diagonals() -> set["Direction"]:
        return {Direction[name] for name in _DIRECTION_DIAGONALS}


class Kind(Enum):
    VERTEX = auto()
    ENTRY = auto()
    EDGE = auto()


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def neighbors(self) -> list["Position"]:
        """
        返回所有相邻的 neighbor 位置（上下左右四个方向）。
        """
        return [
            Position(self.x - 1, self.y),  # 上
            Position(self.x + 1, self.y),  # 下
            Position(self.x, self.y - 1),  # 左
            Position(self.x, self.y + 1)  # 右
        ]

    def kind(self) -> Kind:
        if self.x % 2 == 0 and self.y % 2 == 0:
            return Kind.VERTEX
        if self.x % 2 == 1 and self.y % 2 == 1:
            return Kind.ENTRY
        return Kind.EDGE

    def move(self, direction: Direction, distance: int = 1) -> "Position":
        dx, dy = direction.to_delta()
        return Position(self.x + dx * distance, self.y + dy * distance)
