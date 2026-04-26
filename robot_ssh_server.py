# Импортирует классы из других модулей:
import time
import RPi.GPIO as GPIO
import paramiko
import socket
import threading
import os
from logging_config import logger
from robot.actuators import Motor

motor = Motor()

COMMANDS = {
    'forward': (motor.forward, "Робот движется вперёд"),
    'backward': (motor.backward, "Робот движется назад"),
    'left': (motor.left, "Робот поворачивает влево"),
    'right': (motor.right, "Робот поворачивает вправо"),
    'stop': (motor.stop, "Робот остановлен")
}

# Настройки SSH
SSH_HOST = '0.0.0.0'
SSH_PORT = 2222
SSH_USERNAME = 'valli'

# Пути к ключам
HOST_KEY_FILE_ED25519 = 'ssh_host_ed25519_key'
HOST_KEY_FILE_RSA = 'ssh_host_rsa_key'
AUTHORIZED_KEYS_FILE = '/home/valli/.ssh/authorized_keys'

# Константы
MAX_COMMAND_LENGTH = 100
MAX_CLIENTS = 5

# === НОВЫЕ НАСТРОЙКИ ДЛЯ ПЛАВНОСТИ ===
COMMAND_DELAY = 0.1  # Задержка между командами (секунды)
ENABLE_COMMAND_QUEUE = True  # Включить очередь команд
# ===================================

def load_authorized_keys():
    """Загружает ключи из файла, сохраняя точный формат"""
    keys = set()
    try:
        if not os.path.exists(AUTHORIZED_KEYS_FILE):
            logger.error(f"Файл не существует: {AUTHORIZED_KEYS_FILE}")
            return keys
            
        with open(AUTHORIZED_KEYS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Очищаем ключ от лишних символов
                    parts = line.split()
                    if len(parts) >= 2:
                        clean_key = f"{parts[0]} {parts[1]}"
                        keys.add(clean_key)
        
        logger.info(f"✅ Загружено {len(keys)} ключей")
        
    except Exception as e:
        logger.error(f"Ошибка загрузки ключей: {e}")
    
    return keys

AUTHORIZED_KEYS = load_authorized_keys()

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.channel = None
        self.last_command_time = 0
        self.command_queue = []  # Очередь команд
        self.processing_lock = threading.Lock()
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_publickey(self, username, key):
        if username != SSH_USERNAME:
            logger.warning(f"Неверный пользователь: {username}")
            return paramiko.AUTH_FAILED
        
        # Формируем строку ключа клиента
        client_key_string = f"{key.get_name()} {key.get_base64()}"
        
        # Проверяем наличие в множестве
        if client_key_string in AUTHORIZED_KEYS:
            logger.info("✅ Аутентификация УСПЕШНА!")
            return paramiko.AUTH_SUCCESSFUL
        
        logger.warning("❌ Ключ не найден в authorized_keys")
        return paramiko.AUTH_FAILED
    
    def get_allowed_auths(self, username):
        return 'publickey'
    
    def check_channel_shell_request(self, channel):
        self.channel = channel
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_command(command):
    """Обработка команд робота с задержкой"""
    command = command.strip().lower()
    
    if len(command) > MAX_COMMAND_LENGTH:
        return "Ошибка: команда слишком длинная"
    
    # Добавляем небольшую задержку для плавности
    time.sleep(COMMAND_DELAY)
    
    func, response = COMMANDS.get(command, (None, f"Неизвестная команда: {command}"))
    if func:
        try:
            func()
            logger.info(f"Выполнена команда: {command}")
            return response
        except Exception as e:
            logger.error(f"Ошибка выполнения '{command}': {e}")
            return f"Ошибка: {str(e)}"
    return response

def handle_command_smart(command, last_command, last_time):
    """Умная обработка команд - игнорирует дубликаты"""
    current_time = time.time()
    
    # Игнорируем одинаковые команды, отправленные слишком часто
    if command == last_command and (current_time - last_time) < 0.3:
        return None, last_command, last_time  # Игнорируем
    
    # Выполняем команду
    response = handle_command(command)
    return response, command, current_time

def ssh_session(client):
    """Обработка SSH сессии для клиента"""
    logger.info(f"Начало сессии для {client.getpeername()}")
    
    transport = None
    channel = None
    
    try:
        transport = paramiko.Transport(client)
        transport.banner_timeout = 30
        transport.auth_timeout = 60
        transport.set_keepalive(30)
        
        # Загружаем хост-ключи
        if os.path.exists(HOST_KEY_FILE_ED25519):
            host_key = paramiko.Ed25519Key(filename=HOST_KEY_FILE_ED25519)
            logger.info("Загружен ED25519 хост-ключ")
        elif os.path.exists(HOST_KEY_FILE_RSA):
            host_key = paramiko.RSAKey(filename=HOST_KEY_FILE_RSA)
            logger.info("Загружен RSA хост-ключ")
        else:
            logger.info("Генерация нового ED25519 хост-ключа...")
            host_key = paramiko.Ed25519Key.generate()
            host_key.write_private_key_file(HOST_KEY_FILE_ED25519)
            logger.info("Создан новый ED25519 ключ")
        
        transport.add_server_key(host_key)
        
        server = SSHServer()
        transport.start_server(server=server)
        
        # Ожидаем канал
        channel = transport.accept(30)
        if channel is None:
            logger.error("Не удалось открыть канал")
            return
        
        logger.info("Канал успешно открыт")
        
        # Ожидаем shell запрос
        if not server.event.wait(30):
            logger.error("Shell запрос не получен")
            return
        
        # Отправляем приветствие
        welcome = "\r\n🤖 Добро пожаловать в управление роботом!\r\n"
        welcome += "📋 Доступные команды:\r\n"
        welcome += "  • forward  - движение вперёд\r\n"
        welcome += "  • backward - движение назад\r\n"
        welcome += "  • left     - поворот налево\r\n"
        welcome += "  • right    - поворот направо\r\n"
        welcome += "  • stop     - остановка\r\n"
        welcome += "  • exit     - выход\r\n\r\n"
        channel.send(welcome.encode())
        
        # Переменные для умной обработки
        last_command = None
        last_command_time = 0
        command_buffer = []
        last_buffer_clear = time.time()
        
        # Основной цикл
        while True:
            try:
                channel.settimeout(30)
                data = channel.recv(1024)
                
                if not data:
                    logger.info("Клиент закрыл соединение")
                    break
                
                command = data.decode('utf-8', errors='replace').strip()
                
                if command.lower() == 'exit':
                    channel.send("До свидания! 👋\r\n".encode())
                    break
                
                if ENABLE_COMMAND_QUEUE:
                    # Режим очереди команд
                    if command == 'stop':
                        # STOP очищает очередь и выполняется сразу
                        command_buffer.clear()
                        response = handle_command(command)
                        channel.send(f"{response}\r\n".encode())
                    else:
                        # Добавляем команду в буфер
                        command_buffer.append(command)
                        
                        # Ограничиваем размер буфера
                        if len(command_buffer) > 5:
                            command_buffer.pop(0)
                        
                        # Обрабатываем последнюю команду в буфере
                        current_time = time.time()
                        if current_time - last_buffer_clear > 0.2:  # Каждые 200мс
                            if command_buffer:
                                last_cmd = command_buffer[-1]
                                response = handle_command(last_cmd)
                                if response:
                                    channel.send(f"{response}\r\n".encode())
                                command_buffer.clear()
                                last_buffer_clear = current_time
                else:
                    # Обычный режим с игнорированием дубликатов
                    response, last_command, last_command_time = handle_command_smart(
                        command, last_command, last_command_time
                    )
                    if response:
                        channel.send(f"{response}\r\n".encode())
                
            except socket.timeout:
                # Таймаут - отправляем keepalive
                continue
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки: {e}")
                break
                
    except Exception as e:
        logger.error(f"Ошибка в SSH сессии: {e}", exc_info=True)
    finally:
        # Останавливаем робота при отключении
        try:
            motor.stop()
        except:
            pass
        
        if channel and not channel.closed:
            channel.close()
        if transport and transport.is_active():
            transport.close()
        logger.info("SSH сессия завершена")

def start_ssh_server():
    """Запуск SSH сервера"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((SSH_HOST, SSH_PORT))
        sock.listen(MAX_CLIENTS)
        sock.settimeout(1.0)
        logger.info(f"🚀 SSH сервер запущен на {SSH_HOST}:{SSH_PORT}")
        logger.info(f"🔑 Авторизованных ключей: {len(AUTHORIZED_KEYS)}")
        logger.info(f"⚙️  Задержка команд: {COMMAND_DELAY}с")
        logger.info(f"📋 Очередь команд: {'Включена' if ENABLE_COMMAND_QUEUE else 'Выключена'}")
        
        if len(AUTHORIZED_KEYS) == 0:
            logger.warning("⚠️  Нет авторизованных ключей! Подключение невозможно!")
            logger.warning(f"📁 Добавьте ключи в {AUTHORIZED_KEYS_FILE}")
            
    except OSError as e:
        logger.critical(f"❌ Не удалось запустить сервер: {e}")
        return
    
    active_threads = []
    
    try:
        while True:
            active_threads = [t for t in active_threads if t.is_alive()]
            
            try:
                client, addr = sock.accept()
                logger.info(f"📡 Новое подключение от {addr}")
                
                if len(active_threads) >= MAX_CLIENTS:
                    logger.warning(f"Лимит подключений ({MAX_CLIENTS}). Отказ {addr}")
                    client.close()
                    continue
                
                thread = threading.Thread(target=ssh_session, args=(client,))
                thread.daemon = True
                thread.start()
                active_threads.append(thread)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Ошибка принятия подключения: {e}")
                
    except KeyboardInterrupt:
        logger.info("🛑 Остановка сервера...")
    finally:
        sock.close()
        logger.info("✅ Сервер остановлен")

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Запуск SSH сервера управления роботом")
    logger.info("="*50)
    
    # Проверяем существование файла с ключами
    if not os.path.exists(AUTHORIZED_KEYS_FILE):
        logger.error(f"❌ Файл не найден: {AUTHORIZED_KEYS_FILE}")
        logger.info("Создайте файл и добавьте публичные ключи:")
        logger.info(f"  mkdir -p /home/valli/.ssh")
        logger.info(f"  echo 'ssh-ed25519 ...' > {AUTHORIZED_KEYS_FILE}")
        logger.info(f"  chmod 600 {AUTHORIZED_KEYS_FILE}")
    
    start_ssh_server()