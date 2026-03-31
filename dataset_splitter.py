import os
import random
import shutil
from tqdm import tqdm  # 进度条库，可通过 pip install tqdm 安装


def split_dataset(
        img_dir="images",  # 原始图片目录
        label_dir="labels",  # 原始标注目录
        output_dir="dataset",  # 输出根目录
        split_ratio=(0.7, 0.15, 0.15),  # 训练:验证:测试比例
        seed=42,  # 随机种子（确保可复现）
        copy=False  # True=复制文件 False=移动文件
):
    # 设置随机种子
    random.seed(seed)

    # 验证参数
    assert abs(sum(split_ratio) - 1.0) < 1e-6, "划分比例总和必须为1"
    assert os.path.exists(img_dir), f"图片目录不存在: {img_dir}"
    assert os.path.exists(label_dir), f"标注目录不存在: {label_dir}"

    # 获取匹配的文件列表（过滤无效文件）
    valid_pairs = []
    img_exts = {".jpg", ".jpeg", ".png", ".bmp"}

    # 遍历图片目录
    for img_file in os.listdir(img_dir):
        base_name, ext = os.path.splitext(img_file)
        if ext.lower() not in img_exts:
            continue

        # 检查对应标注文件
        label_file = f"{base_name}.txt"
        label_path = os.path.join(label_dir, label_file)
        if os.path.exists(label_path):
            valid_pairs.append((img_file, label_file))
        else:
            print(f"警告: 缺失标注文件 {label_file}")

    # 打乱顺序
    random.shuffle(valid_pairs)
    total = len(valid_pairs)
    print(f"找到有效数据对: {total} 个")

    # 计算划分点
    train_end = int(total * split_ratio[0])
    val_end = train_end + int(total * split_ratio[1])

    # 创建目录结构
    dirs = {
        "train": os.path.join(output_dir, "train"),
        "val": os.path.join(output_dir, "val"),
        "test": os.path.join(output_dir, "test")
    }
    for d in dirs.values():
        os.makedirs(os.path.join(d, "images"), exist_ok=True)
        os.makedirs(os.path.join(d, "labels"), exist_ok=True)

    # 文件操作函数
    file_op = shutil.copy2 if copy else shutil.move

    # 分发文件
    def process_files(files, split_name):
        for img_file, label_file in tqdm(files, desc=split_name):
            # 源路径
            src_img = os.path.join(img_dir, img_file)
            src_label = os.path.join(label_dir, label_file)

            # 目标路径
            dest_dir = dirs[split_name]
            dest_img = os.path.join(dest_dir, "images", img_file)
            dest_label = os.path.join(dest_dir, "labels", label_file)

            try:
                file_op(src_img, dest_img)
                file_op(src_label, dest_label)
            except Exception as e:
                print(f"处理失败 {img_file}: {str(e)}")

    # 划分数据集
    splits = {
        "train": valid_pairs[:train_end],
        "val": valid_pairs[train_end:val_end],
        "test": valid_pairs[val_end:]
    }

    # 执行分发
    for split_name, files in splits.items():
        process_files(files, split_name)

    print("数据集划分完成！")
    print(f"最终分布：训练集 {len(splits['train'])}，验证集 {len(splits['val'])}，测试集 {len(splits['test'])}")


if __name__ == "__main__":
    # 使用示例（修改这些参数）
    split_dataset(
        img_dir="./data/dataset/images",  # 修改为实际图片路径
        label_dir="./data/dataset/labels",  # 修改为实际标注路径
        output_dir="./split_dataset",  # 输出目录名称
        split_ratio=(0.7, 0.15, 0.15),  # 划分比例
        seed=41,  # 随机种子
        copy=True  # True=复制模式 False=移动模式
    )