import argparse
import importlib
from pathlib import Path


def parse_dataset_yaml(data_yaml: Path):
    """轻量解析path/train/val/test，避免额外依赖。"""
    values = {}
    for raw_line in data_yaml.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in {"path", "train", "val", "test"}:
            values[key] = value.strip().strip('"').strip("'")
    return values


def labels_dir_from_images(images_dir: Path):
    if images_dir.name == "images":
        return images_dir.parent / "labels"
    return images_dir.parent / "labels"


def validate_dataset_structure(data_yaml: Path):
    if not data_yaml.exists():
        raise FileNotFoundError(f"数据集配置不存在: {data_yaml}")

    conf = parse_dataset_yaml(data_yaml)
    root = Path(conf.get("path", ""))
    if not root.exists():
        raise FileNotFoundError(f"数据集根目录不存在: {root}")

    missing = []
    for split in ("train", "val", "test"):
        rel = conf.get(split)
        if not rel:
            continue
        images_dir = root / rel
        labels_dir = labels_dir_from_images(images_dir)
        if not images_dir.exists():
            missing.append(str(images_dir))
        if not labels_dir.exists():
            missing.append(str(labels_dir))

    if missing:
        msg = "\n".join(missing)
        raise FileNotFoundError(f"数据集目录缺失:\n{msg}")

    print(f"[OK] 数据集校验通过: {root}")


def clear_dataset_cache_files(data_yaml: Path):
    """清理YOLO数据缓存，修复不同numpy版本导致的缓存反序列化错误。"""
    conf = parse_dataset_yaml(data_yaml)
    root = Path(conf.get("path", ""))
    if not root.exists():
        return 0

    removed = 0
    for split in ("train", "val", "test"):
        rel = conf.get(split)
        if not rel:
            continue

        images_dir = root / rel
        labels_dir = labels_dir_from_images(images_dir)
        scan_dirs = [images_dir, labels_dir, images_dir.parent]

        for d in scan_dirs:
            if not d.exists():
                continue
            for p in d.glob("*.cache"):
                try:
                    p.unlink()
                    removed += 1
                except OSError:
                    pass

    if removed:
        print(f"[INFO] 已清理数据缓存文件: {removed} 个")
    return removed


def resolve_resume_checkpoint(custom_checkpoint: str | None):
    if custom_checkpoint:
        ckpt = Path(custom_checkpoint)
    else:
        ckpt = Path("runs/detect/train/weights/last.pt")

    if not ckpt.exists():
        raise FileNotFoundError(
            f"未找到可续训的checkpoint: {ckpt}\n"
            "请先进行一次训练，或通过 --checkpoint 指定 last.pt。"
        )
    return ckpt


def raise_checkpoint_compat_error(exc: Exception, checkpoint: Path):
    msg = str(exc)
    if "C3k2" in msg or "Can't get attribute" in msg:
        raise RuntimeError(
            "续训失败：当前ultralytics版本与checkpoint结构不兼容。\n"
            f"checkpoint: {checkpoint}\n"
            "建议执行以下步骤后重试：\n"
            "1) python -m pip install -U ultralytics\n"
            "2) python train.py --resume\n"
            "若仍失败，请使用与该checkpoint相同版本的ultralytics环境。"
        ) from exc
    raise


def build_args():
    parser = argparse.ArgumentParser(description="YOLOv8 训练脚本（支持断点续训）")
    parser.add_argument("--data", default="./config/rice_disease.yaml", help="数据集yaml路径")
    parser.add_argument("--model", default="yolov8n.pt", help="基础权重路径")
    parser.add_argument("--epochs", type=int, default=65, help="训练轮数")
    parser.add_argument("--imgsz", type=int, default=640, help="输入分辨率")
    parser.add_argument("--batch", type=int, default=16, help="batch size")
    parser.add_argument("--workers", type=int, default=0, help="dataloader workers，Windows建议0")
    parser.add_argument("--device", default="cuda", help="cuda 或 cpu")
    parser.add_argument("--project", default="runs/detect", help="输出目录")
    parser.add_argument("--name", default="train", help="实验名")
    parser.add_argument("--resume", action="store_true", help="是否断点续训")
    parser.add_argument("--checkpoint", default=None, help="自定义last.pt路径")
    parser.add_argument("--validate-only", action="store_true", help="仅校验数据集目录")
    return parser.parse_args()


def patch_ultralytics_callbacks():
    """在可选集成异常时自动降级，避免因tensorboard/tensorflow冲突导致训练中断。"""
    import ultralytics.utils.callbacks as cb_pkg
    from ultralytics.utils.callbacks import base as cb_base
    from ultralytics.utils.callbacks.hub import callbacks as hub_cb

    def safe_import_callbacks(mod_name: str):
        try:
            mod = importlib.import_module(f"ultralytics.utils.callbacks.{mod_name}")
            return getattr(mod, "callbacks", None)
        except Exception as exc:
            print(f"[WARN] 跳过回调 {mod_name}: {exc}")
            return None

    def add_integration_callbacks_safe(instance):
        callbacks_list = [hub_cb]

        if "Trainer" in instance.__class__.__name__:
            for name in ("clearml", "comet", "dvc", "mlflow", "neptune", "raytune", "tensorboard", "wb"):
                cb = safe_import_callbacks(name)
                if cb:
                    callbacks_list.append(cb)

        for callbacks in callbacks_list:
            for k, v in callbacks.items():
                if v not in instance.callbacks[k]:
                    instance.callbacks[k].append(v)

    cb_base.add_integration_callbacks = add_integration_callbacks_safe
    cb_pkg.add_integration_callbacks = add_integration_callbacks_safe


def main():
    args = build_args()
    data_yaml = Path(args.data)
    validate_dataset_structure(data_yaml)

    if args.validate_only:
        print("仅校验完成，未开始训练。")
        return

    try:
        from ultralytics import YOLO
        patch_ultralytics_callbacks()

        if args.resume:
            checkpoint = resolve_resume_checkpoint(args.checkpoint)
            print(f"[RESUME] 从checkpoint继续训练: {checkpoint}")
            try:
                model = YOLO(str(checkpoint))
                model.train(resume=True)
            except (AttributeError, ModuleNotFoundError) as exc:
                raise_checkpoint_compat_error(exc, checkpoint)
        else:
            print(f"[TRAIN] 从基础权重开始训练: {args.model}")
            model = YOLO(args.model)

            train_kwargs = {
                "data": str(data_yaml),
                "epochs": args.epochs,
                "imgsz": args.imgsz,
                "batch": args.batch,
                "workers": args.workers,
                "device": args.device,
                "project": args.project,
                "name": args.name,
            }

            try:
                model.train(**train_kwargs)
            except ModuleNotFoundError as exc:
                if "numpy._core" in str(exc):
                    print("[WARN] 检测到numpy缓存兼容问题，正在清理*.cache后重试...")
                    clear_dataset_cache_files(data_yaml)
                    model.train(**train_kwargs)
                else:
                    raise

        model.val(data=str(data_yaml), imgsz=args.imgsz, batch=args.batch, device=args.device)

    except KeyboardInterrupt:
        print("\n训练已暂停。你可以用以下命令继续:")
        print("python train.py --resume")


if __name__ == "__main__":
    main()
