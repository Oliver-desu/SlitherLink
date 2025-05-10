from typing import List, Dict

from edge_count import *
from pos import *


class Sudoku:
    """
    表示一个带边界信息的数独棋盘。
    - size: Tuple[int, int]
        数独棋盘的格子尺寸，(行数, 列数)。
    - total_size: Tuple[int, int]
        整体棋盘尺寸，包含顶点和边，计算公式为 (2 * 行数 + 1, 2 * 列数 + 1)。
    - entry: Dict[Position, int]
        记录每个格子中的数字，key 是格子中心的坐标 (奇数行, 奇数列)，value 是 0~3 的数字。
    - edge: Dict[Position, EdgeType]
        记录每条边的位置及其类型，key 是边的位置 (偶数行+奇数列 或 奇数行+偶数列)，
        value 是 EdgeType，表示该边当前的状态（例如实线、空格或交叉）。
    - edge_count: Dict[Tuple[Position, Direction], EdgeCount]
        记录每个格子的四个角的边界条件，
        key 是 (格子中心位置, 角的方向)，value 是 EdgeCount，表示该角可能有多少条实线边。
    """

    def __init__(self, grid: List[List[int]]):
        """
        根据给定的 grid 初始化数独棋盘。
        - grid: List[List[int]]
            输入的初始数字矩阵，每个元素为 0~3 之间的整数。
        """
        h, w = (len(grid), len(grid[0]) if grid else 0)
        self.size = h, w
        self.total_size = (2 * h + 1, 2 * w + 1)
        self.entry: Dict[Position, int] = {}
        self.edge: Dict[Position, EdgeType] = {}
        self.edge_count: Dict[Tuple[Position, Direction], EdgeCount] = {}

        # 读取数独格子
        for i in range(h):
            for j in range(w):
                value = grid[i][j]
                if value not in (0, 1, 2, 3):
                    continue
                pos = Position(2 * i + 1, 2 * j + 1)
                self.entry[pos] = value

        # 初始化边
        for i in range(2 * h + 1):
            for j in range(2 * w + 1):
                pos = Position(i, j)
                if pos.kind() == Kind.EDGE:
                    self.edge[pos] = EdgeType.SPACE

        # 初始化角落 EdgeCount
        for pos in self.entry.keys():
            for direction in Direction.diagonals():
                self.edge_count[(pos, direction)] = EdgeCount.ANY

    @classmethod
    def from_file(cls, file_path: str) -> "Sudoku":
        """
        从文本文件读取 grid 并创建 Sudoku 对象。
        """
        grid = []
        with open(file_path, 'r') as f:
            for line in f:
                numbers = [int(x) for x in line.strip().split()]
                grid.append(numbers)
        return cls(grid)

    def display(self, scale: Tuple[int, int] = (1, 0)) -> None:
        """
        打印当前棋盘状态，按照指定比例（scale）缩放显示。
        - scale: (行缩放, 列缩放)，分别控制横向和纵向的显示间距。
        """
        rows, cols = self.total_size
        row_scale, col_scale = scale

        for i in range(rows):
            if i % 2 == 0:
                # 输出顶点和横边
                line = ''
                for j in range(cols):
                    if j % 2 == 0:
                        line += '*'
                    else:
                        line += self.edge.get(Position(i, j)).to_str(row_scale)
                print(line)
            else:
                # 输出竖边和格子内容
                num_line = 2 * col_scale + 1
                lines = ['' for _ in range(num_line)]
                for j in range(cols):
                    for loc in range(num_line):
                        if j % 2 == 0:
                            lines[loc] += self.edge.get(Position(i, j)).to_str(col_scale, loc)
                        else:
                            lines[loc] += self._draw_entry(Position(i, j), (row_scale, col_scale), loc)
                for line in lines:
                    print(line)

    def _draw_entry(self, pos: Position, scale: Tuple[int, int], loc: int) -> str:
        """
        绘制指定格子的位置内容，包括数字和角落的 EdgeCount。
        """
        row_scale, col_scale = scale
        entry_num = self.entry.get(pos, -1)
        if entry_num > 0:
            if loc == col_scale:
                # 中间行显示格子数字
                return row_scale * ' ' + f"{entry_num}" + row_scale * ' '
            elif loc == 0:
                # 顶部显示左上角和右上角的 EdgeCount
                x = self.edge_count.get((pos, Direction.UP_LEFT))
                y = self.edge_count.get((pos, Direction.UP_RIGHT))
                return str(x) + (2 * row_scale - 1) * ' ' + str(y)
            elif loc == 2 * col_scale:
                # 底部显示左下角和右下角的 EdgeCount
                x = self.edge_count.get((pos, Direction.DOWN_LEFT))
                y = self.edge_count.get((pos, Direction.DOWN_RIGHT))
                return str(x) + (2 * row_scale - 1) * ' ' + str(y)
        return (2 * row_scale + 1) * ' '


if __name__ == "__main__":
    sudoku = Sudoku.from_file("example_puzzle.txt")
    sudoku.display()
