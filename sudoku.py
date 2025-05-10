from typing import Callable, List, Dict, Any

from edge_count import *
from pos import *

Command = Tuple[Callable[..., None], Tuple[Any, ...]]


class Sudoku:
    """
    表示一个带边界信息的数独棋盘。

    属性:
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
    - command_stack: List[Command]
        维护一系列等待执行的推导命令，支持批量逻辑推导。

    方法:
    - set_edge(pos, edge_type): 尝试设置一条边，若成功修改返回 True。
    - set_edge_count(pos, direction, ec): 尝试设置一组边数限制，若成功修改返回 True。
    - deduce_from_corner(pos, direction): 基于角的边信息进行推导。
    - deduce_from_vertex(pos): 基于顶点的边信息进行推导。
    - deduce_from_entry(pos): 基于格子内部数字进行推导。
    - add_command(func, *args): 将推导命令加入栈中。
    - run_next_command(): 执行栈顶命令。
    - run_all_commands(): 执行所有命令直到栈空。
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
        self.command_stack: List[Command] = []

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
        if entry_num >= 0:
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

    def set_edge(self, pos: Position, edge_type: EdgeType) -> bool:
        """
        尝试设置 pos 位置处的边类型（edge type）。
        - 如果当前位置是 SPACE（可修改），则更新为指定的 edge_type，返回 True。
        - 如果当前位置不是 SPACE（不可修改），不进行更改，返回 False。
        """
        if self.edge.get(pos, -1) == EdgeType.SPACE:
            self.edge[pos] = edge_type
            return True
        return False

    def set_edge_count(self, pos: Position, direction: Direction, ec: EdgeCount) -> bool:
        """
        尝试设置 pos 位置在指定方向 direction 上的边计数（edge count）。
        - 如果当前位置已有 edge count，且与新 ec 不同，则取交集并更新。
        - 如果交集为空，说明矛盾，抛出 ValueError。
        - 如果已有值与新值相同，不做更改，返回 False。
        """
        curr_ec = self.edge_count.get((pos, direction))
        if curr_ec and curr_ec != ec:
            new_ec = curr_ec.intersect(ec)
            if new_ec:
                self.edge_count[(pos, direction)] = new_ec
                return True
            else:
                raise ValueError("Sudoku reached a contradiction!")
        return False

    def add_command(self, func: Callable[..., None], *args: Any):
        """
        将一个新的推导命令加入栈中。
        """
        self.command_stack.append((func, args))

    def run_next_command(self):
        """
        执行栈顶的推导命令。
        """
        if not self.command_stack:
            return
        func, args = self.command_stack.pop()
        func(*args)

    def run_all_commands(self):
        """
        执行所有推导命令，直到栈空。
        """
        while self.command_stack:
            self.run_next_command()

    def deduce_from_corner(self, pos: Position, direction: Direction) -> None:
        """
        根据一个 corner 点和方向，结合已有边的信息，推导 edge 和 edge_count 的新状态。
        """
        # 获取当前 corner 的 edge count 信息
        ec = self.edge_count.get((pos, direction))
        if not ec:
            return

        # 获取当前方向左右两条边
        pos1 = pos.move(direction.rotate(step=-1))  # 左边
        pos2 = pos.move(direction.rotate(step=1))  # 右边
        edge1 = self.edge.get(pos1)
        edge2 = self.edge.get(pos2)

        # 计算推导结果
        new_ec = edge1.add(edge2)
        new_edge1 = ec.subtract(edge2)
        new_edge2 = ec.subtract(edge1)

        # 应用推导结果，更新棋盘状态
        self.set_edge_count(pos, direction, new_ec)
        self.set_edge(pos1, new_edge1)
        self.set_edge(pos2, new_edge2)

    def deduce_from_vertex(self, pos: Position) -> None:
        """
        根据顶点 (vertex) 周围的边状态进行逻辑推导。
        """
        dct = {EdgeType.CROSS: [], EdgeType.SPACE: [], EdgeType.THICK: []}
        for edge_pos in pos.neighbors():
            edge = self.edge.get(edge_pos)
            if edge:
                dct[edge].append(edge_pos)

        if len(dct[EdgeType.THICK]) == 2:
            # 如果已有两条实线，则剩余空边必须为叉
            for edge_pos in dct[EdgeType.SPACE]:
                self.set_edge(edge_pos, EdgeType.CROSS)
        elif len(dct[EdgeType.THICK]) == 1 and len(dct[EdgeType.SPACE]) == 1:
            # 如果已有一条实线且一条空边，则空边必须为实线
            for edge_pos in dct[EdgeType.SPACE]:
                self.set_edge(edge_pos, EdgeType.THICK)
        elif len(dct[EdgeType.THICK]) == 0 and len(dct[EdgeType.SPACE]) == 1:
            # 如果无实线且一条空边，则空边必须为叉
            for edge_pos in dct[EdgeType.SPACE]:
                self.set_edge(edge_pos, EdgeType.CROSS)

    def deduce_from_entry(self, pos: Position) -> None:
        """
        根据格子 (entry) 中的数字进行逻辑推导。
        """
        entry_num = self.entry.get(pos)
        if entry_num is None:
            return

        dct = {EdgeType.CROSS: [], EdgeType.SPACE: [], EdgeType.THICK: []}
        for edge_pos in pos.neighbors():
            edge = self.edge.get(edge_pos)
            if edge:
                dct[edge].append(edge_pos)

        if len(dct[EdgeType.THICK]) == entry_num:
            # 如果已有的实线数等于 entry 数字，剩余空边必须为叉
            for edge_pos in dct[EdgeType.SPACE]:
                self.set_edge(edge_pos, EdgeType.CROSS)
        elif len(dct[EdgeType.THICK]) + len(dct[EdgeType.SPACE]) == entry_num:
            # 如果已有实线数 + 空边数等于 entry 数字，空边必须为实线
            for edge_pos in dct[EdgeType.SPACE]:
                self.set_edge(edge_pos, EdgeType.THICK)

    def propagate_diagonal(self, pos: Position, direction: Direction) -> None:
        """
        沿指定对角方向，递归推导并更新 edge count。
        - 读取当前格子反方向的 edge count（作为初值）。
        - 根据当前 entry 数字，推算出本方向的 edge count。
        - 更新本方向的 edge count，并将变化传递到对角方向的下一个格子。
        - 如果推导成功，继续递归传播。
        """
        # 根据 entry 数字推导前方向的 edge count
        entry_num = self.entry.get(pos, -1)
        if entry_num not in (1, 2, 3):
            return

        # 获取当前位置反方向的 edge count
        ec0 = self.edge_count.get((pos, direction.opposite()))
        ec1 = ec0.subtract_by(entry_num)

        if self.set_edge_count(pos, direction, ec1):
            # 如果成功修改，递归推导下一个位置
            next_pos = pos.move(direction, 2)
            ec2 = ec1.flip()
            if self.set_edge_count(next_pos, direction.opposite(), ec2):
                self.propagate_diagonal(next_pos, direction)

    def solve(self):
        """
        将初始推导任务加入指令栈，并执行所有推导。
        """
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                pos = Position(2 * i + 1, 2 * j + 1)
                entry_num = self.entry.get(pos, -1)

                if entry_num in (1, 3):
                    for direction in Direction.diagonals():
                        self.add_command(self.propagate_diagonal, pos, direction)
                elif entry_num == 0:
                    self.add_command(self.deduce_from_entry, pos)

        self.run_all_commands()


if __name__ == "__main__":
    sudoku = Sudoku.from_file("example_puzzle.txt")
    sudoku.solve()
    sudoku.display((4, 1))
