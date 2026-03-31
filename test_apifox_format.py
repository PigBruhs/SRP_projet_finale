#!/usr/bin/env python3
"""
测试Apifox格式的病虫害识别接口
"""

import requests
import json
import time
from pathlib import Path

class ApifoxFormatTester:
    """Apifox格式接口测试器"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """测试健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_pest_identify(self, image_path, region="测试区域"):
        """测试病虫害识别接口"""
        try:
            with open(image_path, "rb") as image_file:
                files = {"image": image_file}
                data = {"region": region}
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/pest/identify",
                    files=files,
                    data=data
                )
                
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_invalid_file(self):
        """测试无效文件"""
        try:
            # 创建一个无效的文件对象
            files = {"image": ("test.txt", "This is not an image", "text/plain")}
            data = {"region": "测试区域"}
            
            response = self.session.post(
                f"{self.base_url}/api/v1/pest/identify",
                files=files,
                data=data
            )
            
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_missing_file(self):
        """测试缺少文件"""
        try:
            data = {"region": "测试区域"}
            
            response = self.session.post(
                f"{self.base_url}/api/v1/pest/identify",
                data=data
            )
            
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """主测试函数"""
    tester = ApifoxFormatTester()
    
    print("=== Apifox格式接口测试 ===\n")
    
    # 1. 健康检查
    print("1. 健康检查:")
    health_result = tester.test_health()
    print(json.dumps(health_result, indent=2, ensure_ascii=False))
    print()
    
    # 2. 查找测试图片
    test_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        test_images.extend(Path('.').glob(f"**/{ext}"))
        test_images.extend(Path('.').glob(f"**/{ext.upper()}"))
    
    if not test_images:
        print("2. 未找到测试图片，跳过图片测试")
        return
    
    # 3. 正常图片测试
    print(f"2. 正常图片测试 (使用: {test_images[0]})")
    result = tester.test_pest_identify(str(test_images[0]))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    # 4. 测试无效文件
    print("3. 无效文件测试:")
    invalid_result = tester.test_invalid_file()
    print(json.dumps(invalid_result, indent=2, ensure_ascii=False))
    print()
    
    # 5. 测试缺少文件
    print("4. 缺少文件测试:")
    missing_result = tester.test_missing_file()
    print(json.dumps(missing_result, indent=2, ensure_ascii=False))
    print()
    
    # 6. 性能测试
    print("5. 性能测试:")
    start_time = time.time()
    for i in range(5):
        result = tester.test_pest_identify(str(test_images[0]))
        success = result.get('code') == 0
        process_time = result.get('data', {}).get('process_time', 0)
        print(f"   第{i+1}次测试: {'成功' if success else '失败'}, 处理时间: {process_time}ms")
    
    total_time = time.time() - start_time
    avg_time = total_time / 5
    print(f"   平均响应时间: {avg_time:.2f}秒")
    print(f"   总耗时: {total_time:.2f}秒")
    
    # 7. 验证响应格式
    print("\n6. 响应格式验证:")
    result = tester.test_pest_identify(str(test_images[0]))
    
    required_fields = ['code', 'msg', 'data']
    data_fields = ['disease_type', 'confidence', 'bbox', 'area', 'severity', 'suggestion', 'model_version', 'process_time']
    bbox_fields = ['x1', 'y1', 'x2', 'y2']
    suggestion_fields = ['immediate', 'long_term']
    
    print("   检查响应结构...")
    for field in required_fields:
        if field in result:
            print(f"   ✅ {field}: 存在")
        else:
            print(f"   ❌ {field}: 缺失")
    
    if 'data' in result:
        print("   检查data字段...")
        for field in data_fields:
            if field in result['data']:
                print(f"   ✅ data.{field}: 存在")
            else:
                print(f"   ❌ data.{field}: 缺失")
        
        if 'bbox' in result['data']:
            print("   检查bbox字段...")
            for field in bbox_fields:
                if field in result['data']['bbox']:
                    print(f"   ✅ data.bbox.{field}: 存在")
                else:
                    print(f"   ❌ data.bbox.{field}: 缺失")
        
        if 'suggestion' in result['data']:
            print("   检查suggestion字段...")
            for field in suggestion_fields:
                if field in result['data']['suggestion']:
                    print(f"   ✅ data.suggestion.{field}: 存在")
                else:
                    print(f"   ❌ data.suggestion.{field}: 缺失")

if __name__ == "__main__":
    main()
