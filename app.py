from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
from PIL import Image
import os
from ultralytics import YOLO
import logging
from datetime import datetime
import json
import time
import torch  # 修复潜在的C0000005崩溃问题

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量
model = None
class_names = [
    "Helminthosporium leaf blight",  # 胡麻叶枯病
    "Bakanae disease",               # 徒长病
    "Rice blast",                    # 稻热病
    "Sheath blight",                 # 纹枯病
    "Sheath rot",                    # 叶鞘腐败病
    "Southern blight",               # 白绢病
    "Bacterial leaf blight",         # 白叶枯病
    "Bacterial leaf streak",         # 细菌性条斑病
    "White tip",                     # 白尖病
    "Root knot nematode",            # 根瘤线虫
    "False smut"                     # 稻曲病
]

def load_model():
    """加载训练好的模型（优先final_models文件夹）"""
    global model
    try:
        # 优先使用final_models中的best.pt和last.pt
        model_paths = [
            "final_models/best.pt",
            "final_models/last.pt",
            "runs/detect/train/weights/best.pt",
            "runs/detect/train/weights/last.pt"
        ]
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        if not model_path:
            raise FileNotFoundError(f"未找到模型文件: {model_paths}")
        print(f"[INFO] 加载模型权重: {model_path}")
        from ultralytics import YOLO
        model = YOLO(model_path)
        logger.info(f"模型加载成功: {model_path}")
        return True
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        return False

def preprocess_image(image_data):
    """预处理图片数据"""
    try:
        # 如果是base64编码的图片
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # 移除data:image/jpeg;base64,前缀
            image_data = image_data.split(',')[1]
        
        # 解码base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 转换为numpy数组
        image_array = np.array(image)
        
        return image_array
    except Exception as e:
        logger.error(f"图片预处理失败: {str(e)}")
        raise ValueError(f"图片格式错误: {str(e)}")

def allowed_file(filename):
    """检查文件格式是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_predictions(results, conf_thres=0.25):
    """格式化预测结果"""
    formatted_results = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                # 获取边界框坐标
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # 获取置信度
                confidence = float(box.conf[0].cpu().numpy())
                
                # 获取类别
                class_id = int(box.cls[0].cpu().numpy())
                class_name = class_names[class_id] if class_id < len(class_names) else f"Unknown_{class_id}"
                
                # 过滤低于阈值的预测
                if confidence < conf_thres:
                    continue
                
                formatted_results.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": round(float(x1), 2),
                        "y1": round(float(y1), 2),
                        "x2": round(float(x2), 2),
                        "y2": round(float(y2), 2)
                    }
                })
    
    return formatted_results

def get_treatment_suggestions(disease_type, severity):
    """根据病害类型和严重程度提供治疗建议"""
    suggestions = {
        "稻瘟病": {
            "immediate": "立即喷洒三环唑或稻瘟灵，隔离病株",
            "long_term": "选用抗病品种，合理密植，加强通风"
        },
        "纹枯病": {
            "immediate": "喷洒井冈霉素或咪鲜胺，清除病叶",
            "long_term": "控制氮肥用量，改善田间通风条件"
        },
        "白叶枯病": {
            "immediate": "喷洒农用链霉素或叶枯唑",
            "long_term": "选用抗病品种，避免深水灌溉"
        },
        "胡麻叶枯病": {
            "immediate": "喷洒多菌灵或甲基托布津",
            "long_term": "合理施肥，增强植株抗病能力"
        },
        "徒长病": {
            "immediate": "喷洒多效唑控制徒长",
            "long_term": "控制氮肥用量，合理密植"
        },
        "叶鞘腐败病": {
            "immediate": "喷洒苯醚甲环唑或嘧菌酯",
            "long_term": "改善排水条件，避免深水灌溉"
        },
        "白绢病": {
            "immediate": "喷洒五氯硝基苯或甲基立枯磷",
            "long_term": "轮作倒茬，改善土壤环境"
        },
        "细菌性条斑病": {
            "immediate": "喷洒农用链霉素或叶枯唑",
            "long_term": "选用抗病品种，避免深水灌溉"
        },
        "白尖病": {
            "immediate": "喷洒多菌灵或甲基托布津",
            "long_term": "合理施肥，增强植株抗病能力"
        },
        "根瘤线虫": {
            "immediate": "使用阿维菌素或噻唑膦灌根",
            "long_term": "轮作倒茬，改善土壤环境"
        },
        "稻曲病": {
            "immediate": "喷洒井冈霉素或咪鲜胺",
            "long_term": "选用抗病品种，合理密植"
        }
    }
    
    # 根据严重程度调整建议
    if severity == "重度":
        immediate = suggestions.get(disease_type, {}).get("immediate", "立即咨询专业农技人员")
        long_term = suggestions.get(disease_type, {}).get("long_term", "加强田间管理")
    elif severity == "中度":
        immediate = suggestions.get(disease_type, {}).get("immediate", "及时采取防治措施")
        long_term = suggestions.get(disease_type, {}).get("long_term", "改善田间管理")
    else:  # 轻度
        immediate = suggestions.get(disease_type, {}).get("immediate", "观察病情发展")
        long_term = suggestions.get(disease_type, {}).get("long_term", "预防为主，加强管理")
    
    return {
        "immediate": immediate,
        "long_term": long_term
    }

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": model is not None
    })

@app.route('/api/v1/pest/identify', methods=['POST'])
def pest_identify():
    """病虫害识别上传接口 - 按照Apifox文档规范"""
    try:
        # 检查模型是否已加载
        if model is None:
            return jsonify({
                "code": 500,
                "msg": "模型未加载，请检查模型文件"
            }), 500
        
        # 获取multipart/form-data数据
        if 'image' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "缺少图片文件"
            }), 400
        
        image_file = request.files['image']
        region = request.form.get('region', '')
        
        if image_file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "未选择文件"
            }), 400
        
        # 验证文件格式
        if not allowed_file(image_file.filename):
            return jsonify({
                "code": 400,
                "msg": "不支持的文件格式，请上传JPG、PNG或BMP格式的图片"
            }), 400
        
        # 读取图片数据
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 转换为numpy数组
        image_array = np.array(image)
        
        # 执行预测（兼容ultralytics 8.0.196，不传conf/iou参数）
        start_time = time.time()
        results = model(image_array)
        process_time = int((time.time() - start_time) * 1000)
        logger.info(f"YOLO原始推理结果: {results}")
        # 格式化结果（手动过滤置信度）
        predictions = format_predictions(results, conf_thres=0.25)
        logger.info(f"格式化后预测结果: {predictions}")

        # 绘制推理结果图片并转为base64
        try:
            # YOLOv8的plot()方法返回PIL.Image
            if hasattr(results, 'plot'):
                result_img = results.plot()
            elif hasattr(results[0], 'plot'):
                result_img = results[0].plot()
            else:
                # 兼容性处理：手动绘制
                result_img = image.copy()
            buffered = io.BytesIO()
            if isinstance(result_img, np.ndarray):
                result_img = Image.fromarray(result_img)
            result_img.save(buffered, format="PNG")
            inference_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            logger.error(f"推理图片生成失败: {str(e)}")
            inference_image_base64 = None

        # 如果没有检测到任何病害
        if not predictions:
            return jsonify({
                "code": 0,
                "msg": "识别成功",
                "data": {
                    "disease_type": "无病害",
                    "confidence": 0.0,
                    "bbox": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0
                    },
                    "area": 0,
                    "severity": "无",
                    "suggestion": {
                        "immediate": "继续观察植株生长状况",
                        "long_term": "保持良好的田间管理"
                    },
                    "model_version": "v2.3",
                    "process_time": process_time,
                    "inference_image": inference_image_base64
                }
            })
        
        # 获取置信度最高的预测结果
        best_prediction = max(predictions, key=lambda x: x['confidence'])
        
        # 计算边界框面积
        bbox = best_prediction['bbox']
        area = int((bbox['x2'] - bbox['x1']) * (bbox['y2'] - bbox['y1']))
        
        # 根据置信度确定严重程度
        confidence = best_prediction['confidence']
        if confidence >= 0.8:
            severity = "重度"
        elif confidence >= 0.6:
            severity = "中度"
        else:
            severity = "轻度"
        
        # 获取病害的中文名称
        disease_name_map = {
            "Helminthosporium leaf blight": "胡麻叶枯病",
            "Bakanae disease": "徒长病",
            "Rice blast": "稻瘟病",
            "Sheath blight": "纹枯病",
            "Sheath rot": "叶鞘腐败病",
            "Southern blight": "白绢病",
            "Bacterial leaf blight": "白叶枯病",
            "Bacterial leaf streak": "细菌性条斑病",
            "White tip": "白尖病",
            "Root knot nematode": "根瘤线虫",
            "False smut": "稻曲病"
        }
        
        disease_type = disease_name_map.get(best_prediction['class_name'], best_prediction['class_name'])
        
        # 根据病害类型提供建议
        suggestions = get_treatment_suggestions(disease_type, severity)
        
        # 返回结果
        response = {
            "code": 0,
            "msg": "识别成功",
            "data": {
                "disease_type": disease_type,
                "confidence": round(confidence, 2),
                "bbox": {
                    "x1": int(bbox['x1']),
                    "y1": int(bbox['y1']),
                    "x2": int(bbox['x2']),
                    "y2": int(bbox['y2'])
                },
                "area": area,
                "severity": severity,
                "suggestion": suggestions,
                "model_version": "v2.3",
                "process_time": process_time,
                "inference_image": inference_image_base64
            }
        }
        
        logger.info(f"识别完成: {disease_type}, 置信度: {confidence:.2f}, 严重程度: {severity}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"识别失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"识别失败: {str(e)}"
        }), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """批量预测接口"""
    try:
        # 检查模型是否已加载
        if model is None:
            return jsonify({
                "success": False,
                "error": "模型未加载，请检查模型文件"
            }), 500
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'images' not in data:
            return jsonify({
                "success": False,
                "error": "缺少图片数据"
            }), 400
        
        images = data['images']
        if not isinstance(images, list):
            return jsonify({
                "success": False,
                "error": "图片数据必须是数组格式"
            }), 400
        
        batch_results = []
        
        for i, image_data in enumerate(images):
            try:
                # 预处理图片
                image_array = preprocess_image(image_data)
                
                # 执行预测
                results = model(image_array, conf=0.25, iou=0.45)
                
                # 格式化结果
                predictions = format_predictions(results)
                
                batch_results.append({
                    "image_index": i,
                    "success": True,
                    "total_detections": len(predictions),
                    "predictions": predictions
                })
                
            except Exception as e:
                batch_results.append({
                    "image_index": i,
                    "success": False,
                    "error": str(e)
                })
        
        # 返回批量结果
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_images": len(images),
            "results": batch_results
        }
        
        logger.info(f"批量预测完成，处理了 {len(images)} 张图片")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"批量预测失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"批量预测失败: {str(e)}"
        }), 500

@app.route('/model_info', methods=['GET'])
def model_info():
    """获取模型信息"""
    if model is None:
        return jsonify({
            "success": False,
            "error": "模型未加载"
        }), 500
    
    try:
        # 获取模型基本信息
        model_info = {
            "model_type": "YOLOv8",
            "classes": class_names,
            "num_classes": len(class_names),
            "model_path": str(model.ckpt_path) if hasattr(model, 'ckpt_path') else "Unknown"
        }
        
        return jsonify({
            "success": True,
            "model_info": model_info
        })
        
    except Exception as e:
        logger.error(f"获取模型信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"获取模型信息失败: {str(e)}"
        }), 500

if __name__ == '__main__':
    # 启动时加载模型
    if load_model():
        logger.info("启动Flask API服务...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        logger.error("模型加载失败，无法启动服务")
