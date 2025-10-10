import os
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def cleanup_old_logs(log_dir: str, days: int = 7):
    """
    지정된 일수보다 오래된 로그 파일 삭제
    
    Args:
        log_dir: 로그 디렉토리 경로
        days: 보관 일수 (기본값: 7일)
    """
    if not os.path.exists(log_dir):
        return
    
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)
    
    for log_file in Path(log_dir).glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
            except Exception:
                pass

class CustomFormatter(logging.Formatter):
    """
    커스텀 로그 포맷터 - 타임스탬프와 1자리 로그 레벨을 포함
    """
    LEVEL_MAP = {
        'DEBUG': 'D',
        'INFO': 'I',
        'WARNING': 'W',
        'ERROR': 'E',
        'CRITICAL': 'C'
    }
    
    def format(self, record):
        record.levelname_short = self.LEVEL_MAP.get(record.levelname, record.levelname[0])
        return super().format(record)
    
    def formatTime(self, record, datefmt=None):
        from datetime import datetime
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%Y-%m-%d %H:%M:%S")
        s = f"{s}.{int(record.msecs):03d}"
        return s

def setup_logger(name: str = None, command_name: str = None) -> logging.Logger:
    """
    환경변수에서 LOG_LEVEL을 읽어서 로거를 설정합니다.
    
    Args:
        name: 로거 이름 (기본값: None)
        command_name: CLI 명령어 이름 (analyze, sequence, crud-matrix 등)
    
    Returns:
        설정된 로거 객체
    """
    # 환경변수에서 로그 레벨 읽기
    log_level_str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    
    # 로그 레벨 매핑
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = log_levels.get(log_level_str, logging.INFO)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 핸들러가 이미 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 포맷터 생성
    formatter = CustomFormatter('%(asctime)s [%(levelname_short)s] : %(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (command_name이 있을 때만)
    if command_name:
        from datetime import datetime
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 7일 이상 된 로그 파일 삭제
        cleanup_old_logs(log_dir, days=7)
        
        # 로그 파일명: {작업명}-YYYYMMDD.log
        log_date = datetime.now().strftime("%Y%m%d")
        log_filename = f"{command_name}-{log_date}.log"
        log_filepath = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 부모 로거로 전파하지 않음 (중복 출력 방지)
    logger.propagate = False
    
    return logger

def get_logger(name: str = None, command_name: str = None) -> logging.Logger:
    """
    로거를 가져옵니다. 환경변수 변경을 반영하기 위해 항상 새로 설정합니다.
    
    Args:
        name: 로거 이름 (기본값: None)
        command_name: CLI 명령어 이름 (analyze, sequence, crud-matrix 등)
    
    Returns:
        로거 객체
    """
    return setup_logger(name, command_name)
