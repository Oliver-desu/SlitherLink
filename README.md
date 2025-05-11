# SlitherLink OCR Solver

本项目用于通过图像识别（OCR）把 SlitherLink 数独题目编成矩阵，并计算解答。

项目分为两大部分：

- `ocr/ocr_script.py`：负责通过模板匹配和 OCR 识别数字，生成整个数独矩阵
- `sudoku/sudoku_solver.py`：负责读取 txt 文件，求解数独，并验证解答

## 目录结构

project_root/
│
├── sudoku/                # 数独相关功能
│   ├── edge_count.py      # 辅助包：边计数
│   ├── pos.py             # 辅助包：位置定义
│   ├── sudoku_solver.py   # 数独求解器
│   └── example_puzzle.txt # 示例数独文件
│
├── ocr/                   # OCR 相关功能
│   ├── images/            # 存放原始数独图像
│   ├── txt/               # 存放 OCR 转换后的文本文件
│   └── ocr_script.py      # 核心 OCR 脚本（批量图片处理）
│
├── main.py                # 主程序入口
├── requirements.txt       # 依赖列表
└── README.md              # 项目说明文档

## 使用方法

### 1. 先用 OCR 处理图像：

```python
from ocr.ocr_script import process_image_grid

process_image_grid([
    ["images/puzzle3-11.jpeg", "images/puzzle3-12.jpeg"],
    ["images/puzzle3-21.jpeg", "images/puzzle3-22.jpeg"],
    ["images/puzzle3-31.jpeg", "images/puzzle3-32.jpeg"],
])
```

生成对应的txt文件（保存在txt文件夹下）

### 2. 解答数独：

```python
from sudoku.sudoku import Sudoku

sudoku = Sudoku.from_file("txt/puzzle3-11.txt")
sudoku.solve()
sudoku.display()

try:
    sudoku.validate_solution()
    print("正确解答！")
except ValueError as e:
    print("解答错误：", e)
```

## 依赖

* OpenCV (`cv2`)
* numpy
* paddleocr

安装方式：

```bash
pip install opencv-python paddleocr paddlepaddle numpy
```

## 备注

* 目前只支持识别数字0-9，若出现读取错误，可选择在 `extract_grid_numbers`中进行小解析优化
* 需要对应的点模板图 `dot_template.jpeg`，存放在images目录

---

任何问题欢迎留言！
