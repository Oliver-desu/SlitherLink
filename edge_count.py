from enum import Enum, auto
from typing import Optional

# --- 外部缓存表 ---
_EDGE_TO_STR_CACHE = {}
_EDGE_TYPE_ADD_TABLE = {
    ("CROSS", "CROSS"): "ZERO",
    ("CROSS", "THICK"): "ONE",
    ("THICK", "CROSS"): "ONE",
    ("THICK", "THICK"): "TWO",
    ("SPACE", "SPACE"): "ANY",
    ("SPACE", "THICK"): "LARGE",
    ("THICK", "SPACE"): "LARGE",
    ("SPACE", "CROSS"): "SMALL",
    ("CROSS", "SPACE"): "SMALL",
}


class EdgeType(Enum):
    THICK = auto()
    SPACE = auto()
    CROSS = auto()

    def add(self, other: EdgeType) -> EdgeCount:
        """
        返回两个 EdgeType 叠加后的 EdgeCount。
        """
        name = _EDGE_TYPE_ADD_TABLE[self.name, other.name]
        return EdgeCount[name]

    def to_str(self, scale: int, loc: int = -1) -> str:
        # 查缓存
        key = (self, scale, loc)
        if key in _EDGE_TO_STR_CACHE:
            return _EDGE_TO_STR_CACHE[key]

        # 需要计算
        if loc == -1:
            length = 2 * scale + 1
            if self == EdgeType.THICK:
                result = '-' * length
            elif self == EdgeType.SPACE:
                result = ' ' * length
            elif self == EdgeType.CROSS:
                result = ' ' * scale + 'x' + ' ' * scale
            else:
                result = ''
        else:
            if self == EdgeType.THICK:
                result = '|'
            elif self == EdgeType.SPACE:
                result = ' '
            elif self == EdgeType.CROSS:
                if scale == loc:
                    result = 'x'
                else:
                    result = ' '
            else:
                result = ''

        # 存缓存
        _EDGE_TO_STR_CACHE[key] = result
        return result


# --- 静态表格 ---
_EC_TO_SET = {
    'ZERO': {0},
    'ONE': {1},
    'TWO': {2},
    'EVEN': {0, 2},
    'SMALL': {0, 1},
    'LARGE': {1, 2},
    'ANY': {0, 1, 2},
}

_SET_TO_EC = {frozenset(v): k for k, v in _EC_TO_SET.items()}

_EC_TO_STR = {
    'ZERO': '0',
    'ONE': '1',
    'TWO': '2',
    'EVEN': 'E',
    'SMALL': 'S',
    'LARGE': 'L',
    'ANY': ' ',
}

_SUBTRACT_BY_TABLE = {
    1: {
        'ZERO': 'ONE',
        'ONE': 'ZERO',
        'TWO': None,
        'EVEN': 'ONE',
        'SMALL': 'SMALL',
        'LARGE': 'ZERO',
        'ANY': 'SMALL',
    },
    2: {
        'ZERO': 'TWO',
        'ONE': 'ONE',
        'TWO': 'ZERO',
        'EVEN': 'EVEN',
        'SMALL': 'LARGE',
        'LARGE': 'SMALL',
        'ANY': 'ANY',
    },
    3: {
        'ZERO': None,
        'ONE': 'TWO',
        'TWO': 'ONE',
        'EVEN': 'ONE',
        'SMALL': 'TWO',
        'LARGE': 'LARGE',
        'ANY': 'LARGE',
    }
}

_SUBTRACT_TABLE = {
    'ONE': {
        EdgeType.THICK: EdgeType.CROSS,
        EdgeType.CROSS: EdgeType.THICK,
    },
    'EVEN': {
        EdgeType.THICK: EdgeType.THICK,
        EdgeType.CROSS: EdgeType.CROSS,
    },
    'SMALL': {
        EdgeType.THICK: EdgeType.CROSS,
    },
    'LARGE': {
        EdgeType.CROSS: EdgeType.THICK,
    }
}


# --- EdgeCount 本体 ---
class EdgeCount(Enum):
    ZERO = auto()
    ONE = auto()
    TWO = auto()
    EVEN = auto()
    SMALL = auto()
    LARGE = auto()
    ANY = auto()

    def subtract(self, edge_type: EdgeType) -> Optional[EdgeType]:
        if self == EdgeCount.ZERO:
            return EdgeType.CROSS
        elif self == EdgeCount.TWO:
            return EdgeType.THICK
        return _SUBTRACT_TABLE[self.name].get(edge_type, None)

    def subtract_by(self, num: int) -> Optional[EdgeCount]:
        if num not in (1, 2, 3):
            raise ValueError(f"SubtractBy only supports 1, 2, or 3, not {num}")
        name = _SUBTRACT_BY_TABLE[num][self.name]
        return EdgeCount[name] if name else None

    def intersect(self, other: EdgeCount) -> Optional[EdgeCount]:
        set_self = self.to_set()
        set_other = other.to_set()
        intersection = set_self & set_other
        return EdgeCount._from_set(intersection)

    def flip(self) -> EdgeCount:
        if self == EdgeCount.ZERO:
            return EdgeCount.EVEN
        if self == EdgeCount.SMALL:
            return EdgeCount.ANY
        return self.subtract_by(2)

    def to_set(self) -> set:
        return _EC_TO_SET[self.name]

    @staticmethod
    def _from_set(values: set) -> Optional[EdgeCount]:
        name = _SET_TO_EC.get(frozenset(values))
        return EdgeCount[name] if name else None

    def __str__(self):
        return _EC_TO_STR.get(self.name, ' ')
