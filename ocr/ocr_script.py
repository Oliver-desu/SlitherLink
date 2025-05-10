import os
from typing import List

import cv2
import numpy as np
from paddleocr import PaddleOCR

# 初始化 PaddleOCR，只初始化一次
ocr_model = PaddleOCR(use_angle_cls=True, lang='en')


def match_template_and_clean(image_path, template_path, threshold: float = 0.8, min_gap: int = 10):
    """
    在图像中匹配指定模板，提取网格坐标并擦除模板点。

    参数:
        image_path (str): 原始图像路径。
        template_path (str): 用于匹配的模板图像路径。
        threshold (float, 可选): 匹配阈值，默认值为 0.8。
        min_gap (int, 可选): 识别为新行/新列所需的最小间距，默认值为 10。

    返回:
        tuple: (grid_size, grid_scale, cleaned_image_path)
            - grid_size (tuple of int): 网格尺寸 (行数, 列数)。
            - grid_scale (tuple of int): 推测的行间距和列间距 (行间距, 列间距)。
            - cleaned_image_path (str): 擦除模板后的图像保存路径。
    """
    # 加载图像
    img = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    x0, y0 = template_gray.shape

    # 执行模板匹配
    result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    x_loc, y_loc = loc

    if len(x_loc) < 5:
        raise ValueError("未找到足够符合要求的模板匹配，请尝试降低匹配阈值。")

    # 初始化匹配结果
    x_indices = [x_loc[0]]
    y_indices = [y_loc[0]]
    x_diff = []
    y_diff = []

    # 根据最小间距提取唯一行列坐标，同时清除模板
    for x, y in zip(x_loc, y_loc):
        if x - x_indices[-1] > min_gap:
            x_diff.append(x - x_indices[-1])
            x_indices.append(x)
        if y - y_indices[-1] > min_gap:
            y_diff.append(y - y_indices[-1])
            y_indices.append(y)

        # 擦除模板点
        top_left = (y, x)
        bottom_right = (y + y0, x + x0)
        cv2.rectangle(img, top_left, bottom_right, (255, 255, 255), thickness=cv2.FILLED)

    # 计算尺度
    grid_size = (len(x_indices) - 1, len(y_indices) - 1)
    grid_scale = (round(sum(x_diff) / len(x_diff)), round(sum(y_diff) / len(y_diff)))

    # 保存处理后的图像
    output_dir = os.path.dirname(image_path)
    output_path = os.path.join(output_dir, f"cleaned_{os.path.basename(image_path)}")
    cv2.imwrite(output_path, img)

    return output_path, grid_size, grid_scale


def extract_grid_numbers(image_path, grid_size, grid_scale, grid_corner=(0, 0)):
    """
    从图像中提取网格中的数字。

    参数:
        image_path (str): 图像路径。
        grid_size (tuple): 网格尺寸 (行数, 列数)。
        grid_scale (tuple): 单元格间距 (水平间距, 垂直间距)。
        grid_corner (tuple, 可选): 网格左上角坐标，默认 (0, 0)。

    返回:
        np.ndarray: 填充了识别数字的矩阵，未识别位置为 -1。
    """
    results = ocr_model.ocr(image_path, cls=True)
    matrix: np.ndarray = np.full(grid_size, -1, dtype=int)

    for row in results:
        for entry in row:
            (x, y) = entry[0][0]  # 取左上角坐标
            col_idx = (int(x) - grid_corner[0]) // grid_scale[0]
            row_idx = (int(y) - grid_corner[1]) // grid_scale[1]

            text = entry[1][0]
            if text.isdigit():
                matrix[row_idx, col_idx] = int(text)
            elif text == "O":
                matrix[row_idx, col_idx] = 0
            elif text == "T":
                matrix[row_idx, col_idx] = 1
            elif text == "E":
                matrix[row_idx, col_idx] = 3
            else:
                print(f"警告: 未知字符 '{text}'，位置 ({row_idx}, {col_idx})，已忽略。")

    return matrix


def process_image_grid(image_grid: List[List[str]], template_path="images/dot_template.jpeg", output_dir="txt"):
    """
    批量处理按网格排列的图像，提取数字矩阵并拼接保存为文本文件。

    参数:
        image_grid (List[List[str]]): 图像路径组成的二维列表，按网格顺序排列。
        template_path (str): 用于模板匹配的点模板图像路径，默认 "images/dot_template.jpeg"。
        output_dir (str): 保存输出文本文件的文件夹，默认 "txt"。

    返回:
        str: 保存的大矩阵文件路径。
    """
    all_combined_rows = []

    for row_paths in image_grid:
        cell_matrices = []
        for img_path in row_paths:
            # 模板匹配并提取小矩阵
            cleaned_path, grid_size, grid_scale = match_template_and_clean(img_path, template_path)
            matrix = extract_grid_numbers(cleaned_path, grid_size, grid_scale)
            cell_matrices.append(matrix)

        # 横向拼接一整行的小矩阵
        combined_row = np.hstack(cell_matrices)
        all_combined_rows.append(combined_row)

    # 纵向拼接所有行
    full_matrix = np.vstack(all_combined_rows)

    # 确定输出文件名
    base_name = os.path.splitext(os.path.basename(image_grid[0][0]))[0]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}.txt")

    # 保存为文本文件
    np.savetxt(output_path, full_matrix, fmt='%s')  # type: ignore

    print(f"数独已保存至: {output_path}")
    return output_path


def process_single_image(img_path: str, template_path="images/dot_template.jpeg", output_dir="txt"):
    """
    处理单张图像，提取数字矩阵并保存为文本文件。

    参数:
        img_path (str): 单张图像的路径。
        template_path (str): 用于模板匹配的点模板图像路径，默认 "images/dot_template.jpeg"。
        output_dir (str): 保存输出文本文件的文件夹，默认 "txt"。

    返回:
        str: 保存的矩阵文件路径。
    """
    return process_image_grid([[img_path]], template_path, output_dir)


if __name__ == "__main__":
    process_single_image("images/puzzle1.jpeg")
    process_single_image("images/puzzle2.jpeg")
