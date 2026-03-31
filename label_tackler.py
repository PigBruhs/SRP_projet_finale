import xml.etree.ElementTree as ET
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
import os
import shutil

# 类别映射字典 (根据你的实际需求修改)
CLASS_MAP = {
    "rDB01": 0,  # 胡麻葉枯病
    "rDF02": 1,  # 徒長病
    "rDP03": 2,  # 稻熱病
    "rDR04": 3,  # 紋枯病
    "rDS05": 4,  # 葉鞘腐敗病
    "rDS06": 5,  # 白絹病
    "rDX07": 6,  # 白葉枯病
    "rDX08": 7,  # 細菌性條斑病
    "rDA09": 8,  # 白尖病
    "rDM10": 9,  # 根瘤線蟲
    "rDU11": 10  # 稻麴病
}


def convert_xml_to_yolo(xml_path, output_dir):
    """核心转换函数"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 解析基础信息
        size = root.find('size')
        width = int(size.find('width').text)
        height = int(size.find('height').text)
        filename = root.find('filename').text

        # 准备输出路径
        txt_path = Path(output_dir) / f"{filename}.txt"

        # 处理所有目标对象
        yolo_lines = []
        for obj in root.findall('object'):
            # 类别转换
            class_name = obj.find('name').text
            class_id = CLASS_MAP.get(class_name, -1)

            if class_id == -1:  # 忽略未定义类别
                continue

            # 解析边界框
            bndbox = obj.find('bndbox')
            xmin = int(bndbox.find('xmin').text)
            ymin = int(bndbox.find('ymin').text)
            xmax = int(bndbox.find('xmax').text)
            ymax = int(bndbox.find('ymax').text)

            # 计算归一化坐标
            x_center = (xmin + xmax) / 2 / width
            y_center = (ymin + ymax) / 2 / height
            w = (xmax - xmin) / width
            h = (ymax - ymin) / height

            # 保留6位小数
            line = f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}"
            yolo_lines.append(line)

        # 写入文件（即使空文件）
        with open(txt_path, 'w') as f:
            f.write('\n'.join(yolo_lines))

        return True

    except Exception as e:
        print(f"转换失败 {xml_path}: {str(e)}")
        return False


def batch_convert(xml_dir, output_dir):
    """批量转换函数"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 遍历所有XML文件
    xml_files = list(Path(xml_dir).glob('**/*.xml'))
    total = len(xml_files)
    success = 0

    for i, xml_path in enumerate(xml_files):
        if convert_xml_to_yolo(xml_path, output_dir):
            success += 1
        print(f"进度: {i + 1}/{total} ({100 * (i + 1) / total:.1f}%)")

    print(f"转换完成！成功: {success}/{total}")

# 使用示例
if __name__ == "__main__":
    XML_DIR = "./dataset/label"  # XML文件所在目录
    OUTPUT_DIR = "./labels"  # 输出目录

    batch_convert(XML_DIR, OUTPUT_DIR)

