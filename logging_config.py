import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def setup_logger():
    """
    Настраивает логер для проекта робота.
    Возвращает экземпляр логера.
    """
    # Создаём логер с именем 'robot'
    logger = logging.getLogger('robot')
    logger.setLevel(logging.DEBUG)  # Записываем все уровни (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    # Удаляем существующие обработчики, чтобы избежать дублирования
    if logger.hasHandlers():
        logger.handlers.clear()

    
    # Путь к файлу лога
    log_file = 'logs/robot.log'
    # log_file = f'robot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log' # временную метку в имя файла

    # Директория для логов (создадим, если нет)
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Обработчик для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,      # 1 МБ на файл
        backupCount=5,           # Хранить до 5 архивных файлов
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)


    # Форматировщик: дата, уровень, модуль, строка, сообщение
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Добавляем обработчик в логер
    logger.addHandler(file_handler)


    # Обработчик для вывода в консоль (только ошибки и предупреждения)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

# Глобальный логер (импортируйте его в других файлах)
logger = setup_logger()

# if __name__ == '__main__':
#     # Пример использования (можно удалить)
#     logger.debug("Отладочная информация")
#     logger.info("Система запущена")
#     logger.warning("Низкий заряд батареи")
#     logger.error("Ошибка связи с сервером")
#     logger.critical("Критическая ошибка!")
