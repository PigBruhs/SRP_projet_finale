import requests
import base64
import json
import time
from pathlib import Path

class RiceDiseaseAPIClient:
    """水稻病害检测API客户端"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_model_info(self):
        """获取模型信息"""
        try:
            response = self.session.get(f"{self.base_url}/model_info")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def predict_single(self, image_path):
        """单张图片预测"""
        try:
            # 使用multipart/form-data格式
            with open(image_path, "rb") as image_file:
                files = {"image": image_file}
                data = {"region": "测试区域"}
                response = self.session.post(
                    f"{self.base_url}/api/v1/pest/identify",
                    files=files,
                    data=data
                )
            
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def predict_batch(self, image_paths):
        """批量图片预测"""
        try:
            results = []
            for image_path in image_paths:
                result = self.predict_single(image_path)
                results.append(result)
            
            return {
                "success": True,
                "total_images": len(image_paths),
                "results": results
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_upload_image(self, image_path):
        """测试文件上传方式"""
        try:
            with open(image_path, "rb") as image_file:
                files = {"image": image_file}
                data = {"region": "测试区域"}
                response = self.session.post(f"{self.base_url}/api/v1/pest/identify", files=files, data=data)
                return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """主测试函数"""
    client = RiceDiseaseAPIClient()
    
    print("=== 水稻病害检测API测试 ===\n")
    
    # 1. 健康检查
    print("1. 健康检查:")
    health_result = client.health_check()
    print(json.dumps(health_result, indent=2, ensure_ascii=False))
    print()
    
    # 2. 获取模型信息
    print("2. 模型信息:")
    model_info = client.get_model_info()
    print(json.dumps(model_info, indent=2, ensure_ascii=False))
    print()
    
    # 3. 查找测试图片
    test_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        test_images.extend(Path('.').glob(f"**/{ext}"))
        test_images.extend(Path('.').glob(f"**/{ext.upper()}"))
    
    if not test_images:
        print("3. 未找到测试图片，跳过预测测试")
        return
    
    # 4. 单张图片预测测试
    print(f"3. 单张图片预测测试 (使用: {test_images[0]})")
    single_result = client.predict_single(str(test_images[0]))
    print(json.dumps(single_result, indent=2, ensure_ascii=False))
    print()
    
    # 5. 批量预测测试
    if len(test_images) > 1:
        print(f"4. 批量预测测试 (使用前2张图片)")
        batch_result = client.predict_batch([str(test_images[0]), str(test_images[1])])
        print(json.dumps(batch_result, indent=2, ensure_ascii=False))
        print()
    
    # 6. 性能测试
    print("5. 性能测试:")
    start_time = time.time()
    for i in range(3):
        result = client.predict_single(str(test_images[0]))
        success = result.get('code') == 0 if 'code' in result else result.get('success', False)
        print(f"   第{i+1}次预测: {'成功' if success else '失败'}")
    
    total_time = time.time() - start_time
    avg_time = total_time / 3
    print(f"   平均预测时间: {avg_time:.2f}秒")
    print(f"   总耗时: {total_time:.2f}秒")

if __name__ == "__main__":
    main()
