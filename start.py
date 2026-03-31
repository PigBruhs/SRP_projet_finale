#!/usr/bin/env python3
"""
水稻病害检测API启动脚本
"""

import os
import sys
import argparse
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'flask', 'ultralytics', 'opencv-python', 
        'pillow', 'numpy', 'torch'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def check_model_files():
    """检查模型文件是否存在"""
    model_paths = [
        "runs/detect/train/weights/best.pt",
        "runs/detect/train/weights/last.pt"
    ]
    
    for path in model_paths:
        if Path(path).exists():
            print(f"✅ 找到模型文件: {path}")
            return True
    
    print("❌ 未找到模型文件")
    print("请确保以下路径之一存在:")
    for path in model_paths:
        print(f"  - {path}")
    return False

def start_api(host='0.0.0.0', port=5000, debug=False):
    """启动API服务"""
    try:
        from app import app, load_model
        
        # 加载模型
        if not load_model():
            print("❌ 模型加载失败")
            return False
        
        print(f"🚀 启动API服务: http://{host}:{port}")
        print("按 Ctrl+C 停止服务")
        
        app.run(host=host, port=port, debug=debug)
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='水稻病害检测API启动脚本')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--check-only', action='store_true', help='仅检查环境，不启动服务')
    
    args = parser.parse_args()
    
    print("=== 水稻病害检测API环境检查 ===\n")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查模型文件
    if not check_model_files():
        sys.exit(1)
    
    print("\n✅ 环境检查通过")
    
    if args.check_only:
        print("环境检查完成，退出")
        return
    
    # 启动服务
    print("\n=== 启动API服务 ===")
    start_api(args.host, args.port, args.debug)

if __name__ == "__main__":
    main()
