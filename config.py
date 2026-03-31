import os

class Config:
    """API配置文件"""
    
    # 基础配置
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000
    
    # 模型配置
    MODEL_PATH = "runs/detect/train/weights/best.pt"
    FALLBACK_MODEL_PATH = "runs/detect/train/weights/last.pt"
    
    # 预测参数
    CONFIDENCE_THRESHOLD = 0.25  # 置信度阈值
    IOU_THRESHOLD = 0.45         # IoU阈值
    
    # 图片处理配置
    MAX_IMAGE_SIZE = 4096        # 最大图片尺寸
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 安全配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大文件大小
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    
    # 性能配置
    WORKERS = 4
    TIMEOUT = 120
    
    @staticmethod
    def get_model_path():
        """获取模型路径，优先使用best.pt"""
        if os.path.exists(Config.MODEL_PATH):
            return Config.MODEL_PATH
        elif os.path.exists(Config.FALLBACK_MODEL_PATH):
            return Config.FALLBACK_MODEL_PATH
        else:
            raise FileNotFoundError("未找到可用的模型文件")
    
    @staticmethod
    def validate_image_format(filename):
        """验证图片格式"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
