# 水稻病害检测API

基于YOLOv8的水稻病害检测REST API服务，支持11种主要水稻病害的自动识别。

## 功能特性

- 🚀 **高性能检测**: 基于YOLOv8的实时病害检测
- 🔍 **多病害识别**: 支持11种主要水稻病害
- 📱 **RESTful API**: 标准HTTP接口，易于集成
- 🖼️ **多种输入**: 支持base64编码和文件上传
- 📊 **批量处理**: 支持单张和批量图片预测
- 🐳 **容器化部署**: 支持Docker和docker-compose
- 📈 **健康监控**: 内置健康检查和性能监控

## 支持的病害类型

| 序号 | 英文名称 | 中文名称 | 类别ID |
|------|----------|----------|---------|
| 0 | Helminthosporium leaf blight | 胡麻叶枯病 | rDB01 |
| 1 | Bakanae disease | 徒长病 | rDF02 |
| 2 | Rice blast | 稻热病 | rDP03 |
| 3 | Sheath blight | 纹枯病 | rDR04 |
| 4 | Sheath rot | 叶鞘腐败病 | rDS05 |
| 5 | Southern blight | 白绢病 | rDS06 |
| 6 | Bacterial leaf blight | 白叶枯病 | rDX07 |
| 7 | Bacterial leaf streak | 细菌性条斑病 | rDX08 |
| 8 | White tip | 白尖病 | rDA09 |
| 9 | Root knot nematode | 根瘤线虫 | rDM10 |
| 10 | False smut | 稻曲病 | rDU11 |

## 快速开始

### 1. 环境要求

- Python 3.8+
- CUDA支持的GPU (推荐)
- 至少4GB内存

### 2. 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd rice-disease-detection-api

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 使用启动脚本
python start.py

# 或直接运行
python app.py
```

服务将在 `http://localhost:5000` 启动

## 模型训练（支持暂停与断点续训）

当前训练配置使用数据集目录：`E:\le projet\Yolo_v8\data\split_dataset`，并要求以下结构：

- `train/images` 和 `train/labels`
- `val/images` 和 `val/labels`
- `test/images` 和 `test/labels`

训练命令：

```bash
python train.py
```

仅校验数据集目录（不训练）：

```bash
python train.py --validate-only
```

训练中可用 `Ctrl+C` 暂停。暂停后使用以下命令从 `last.pt` 继续：

```bash
python train.py --resume
```

如果 `last.pt` 不在默认位置，可手动指定：

```bash
python train.py --resume --checkpoint runs/detect/train/weights/last.pt
```

若续训时报错 `Can't get attribute 'C3k2'`，通常是 checkpoint 与当前 `ultralytics` 版本不兼容。请先升级后重试：

```bash
python -m pip install -U ultralytics
python train.py --resume
```

## API接口文档

### 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **图片格式**: 支持JPG、PNG、BMP等格式

### 接口列表

#### 1. 健康检查

```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "model_loaded": true
}
```

#### 2. 获取模型信息

```http
GET /model_info
```

**响应示例**:
```json
{
  "success": true,
  "model_info": {
    "model_type": "YOLOv8",
    "classes": ["Helminthosporium leaf blight", "Bakanae disease", ...],
    "num_classes": 11,
    "model_path": "runs/detect/train/weights/best.pt"
  }
}
```

#### 3. 病虫害识别上传

```http
POST /api/v1/pest/identify
```

**请求格式**: `multipart/form-data`

**参数**:
- `image`: 图片文件 (支持JPG、PNG、BMP格式)
- `region`: 地区信息 (可选)

**响应示例**:
```json
{
  "code": 0,
  "msg": "识别成功",
  "data": {
    "disease_type": "稻瘟病",
    "confidence": 0.95,
    "bbox": {
      "x1": 100,
      "y1": 100,
      "x2": 300,
      "y2": 300
    },
    "area": 40000,
    "severity": "中度",
    "suggestion": {
      "immediate": "摘除病叶，喷洒三环唑",
      "long_term": "定期巡检，加强通风"
    },
    "model_version": "v2.3",
    "process_time": 200
  }
}
```

#### 4. 批量图片预测

```http
POST /predict_batch
```

**请求体**:
```json
{
  "images": [
    "base64_encoded_image_1",
    "base64_encoded_image_2"
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00",
  "total_images": 2,
  "results": [
    {
      "image_index": 0,
      "success": true,
      "total_detections": 1,
      "predictions": [...]
    },
    {
      "image_index": 1,
      "success": true,
      "total_detections": 0,
      "predictions": []
    }
  ]
}
```

## 使用示例

### Python客户端

```python
import requests

# 发送预测请求
with open("rice_image.jpg", "rb") as f:
    files = {"image": f}
    data = {"region": "测试区域"}
    
    response = requests.post(
        "http://localhost:5000/api/v1/pest/identify",
        files=files,
        data=data
    )

result = response.json()
if result['code'] == 0:
    print(f"识别结果: {result['data']['disease_type']}")
    print(f"置信度: {result['data']['confidence']}")
    print(f"严重程度: {result['data']['severity']}")
else:
    print(f"识别失败: {result['msg']}")
```

### JavaScript客户端

```javascript
// 发送预测请求
async function predictDisease(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('region', '测试区域');
    
    const response = await fetch('http://localhost:5000/api/v1/pest/identify', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// 使用示例
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        const result = await predictDisease(file);
        if (result.code === 0) {
            console.log('识别结果:', result.data.disease_type);
            console.log('置信度:', result.data.confidence);
            console.log('严重程度:', result.data.severity);
        } else {
            console.error('识别失败:', result.msg);
        }
    }
});
```

### cURL测试

```bash
# 健康检查
curl http://localhost:5000/health

# 病虫害识别
curl -X POST http://localhost:5000/api/v1/pest/identify \
  -F "image=@rice_image.jpg" \
  -F "region=测试区域"
```

## 部署指南

### Docker部署

#### 1. 构建镜像

```bash
docker build -t rice-disease-api .
```

#### 2. 运行容器

```bash
docker run -d \
  --name rice-disease-api \
  -p 5000:5000 \
  -v $(pwd)/runs:/app/runs \
  rice-disease-api
```

#### 3. 使用docker-compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f rice-disease-api

# 停止服务
docker-compose down
```

### 生产环境部署

#### 1. 使用Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 2. 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 使用Systemd服务

```ini
[Unit]
Description=Rice Disease Detection API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 性能优化

### 1. GPU加速

确保安装CUDA版本的PyTorch：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 模型优化

- 使用TensorRT进行推理加速
- 启用半精度推理 (FP16)
- 调整置信度和IoU阈值

### 3. 缓存策略

- 使用Redis缓存预测结果
- 实现图片预处理缓存
- 添加结果缓存机制

## 监控和日志

### 1. 健康检查

```bash
curl http://localhost:5000/health
```

### 2. 性能监控

- 预测响应时间
- 内存使用情况
- GPU利用率

### 3. 日志配置

日志级别可通过环境变量设置：

```bash
export LOG_LEVEL=DEBUG
```

## 故障排除

### 常见问题

#### 1. 模型加载失败

- 检查模型文件路径
- 确认模型文件完整性
- 检查CUDA环境

#### 2. 内存不足

- 减少batch size
- 使用CPU推理
- 增加系统内存

#### 3. 预测结果不准确

- 检查训练数据质量
- 调整置信度阈值
- 重新训练模型

### 调试模式

```bash
python start.py --debug
```

## 开发指南

### 1. 添加新的病害类型

1. 在`class_names`列表中添加新类别
2. 更新训练数据集
3. 重新训练模型

### 2. 自定义预处理

修改`preprocess_image`函数以适应特定需求

### 3. 扩展API功能

在`app.py`中添加新的路由和功能

## 许可证

本项目采用MIT许可证

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- 项目维护者: 张琨博
- 邮箱: [your-email@example.com]
- 项目地址: [your-repo-url]
