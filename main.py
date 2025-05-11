# main.py

from ocr.ocr_script import process_image_grid
from sudoku.sudoku import Sudoku


def main():
    # === 第一步：OCR 识别所有小图像并生成大矩阵 ===
    image_grid = [
        ["images/puzzle3-11.jpeg", "images/puzzle3-12.jpeg"],
        ["images/puzzle3-21.jpeg", "images/puzzle3-22.jpeg"],
        ["images/puzzle3-31.jpeg", "images/puzzle3-32.jpeg"],
    ]

    # 处理图像，得到大矩阵txt路径
    ocr_output_path = process_image_grid(image_grid)

    # === 第二步：读取OCR识别后的大矩阵，加载为数独对象 ===
    sudoku = Sudoku.from_file(ocr_output_path)

    # === 第三步：求解数独并显示 ===
    sudoku.solve()
    sudoku.display()

    # === 第四步：验证解答是否正确 ===
    try:
        sudoku.validate_solution()
        print("正确解答！")
    except ValueError as e:
        print("解答错误：", e)


if __name__ == "__main__":
    main()
