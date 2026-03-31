import requests
import os

def test_api():
    # 查找测试图片
    test_images = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                test_images.append(os.path.join(root, file))
                if len(test_images) >= 3:  # 只取前3张
                    break
        if len(test_images) >= 3:
            break
    
    if not test_images:
        print("未找到测试图片，请确保项目目录中有图片文件")
        return
    
    print(f"找到测试图片: {test_images[0]}")
    
    # 准备请求数据
    url = "http://localhost:5000/api/v1/pest/identify"
    
    with open(test_images[0], 'rb') as f:
        files = {'image': (os.path.basename(test_images[0]), f, 'image/jpeg')}
        data = {'region': '广东'}
        
        print("正在发送请求...")
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("请求成功！")
                print(f"响应数据: {result}")
            else:
                print(f"请求失败: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
        except requests.exceptions.Timeout as e:
            print(f"请求超时: {e}")
        except Exception as e:
            print(f"其他错误: {e}")

if __name__ == "__main__":
    test_api()
