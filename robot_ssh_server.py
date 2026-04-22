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
    'stop': (motor.stop, "Робот остановлен"),
    'exit': ()
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

def load_authorized_keys():
    """Загружает ключи из файла, очищая от невидимых символов"""
    keys = set()
    try:
        if not os.path.exists(AUTHORIZED_KEYS_FILE):
            logger.error(f"Файл не существует: {AUTHORIZED_KEYS_FILE}")
            return keys
            
        with open(AUTHORIZED_KEYS_FILE, 'r') as f:
            for line in f:
                # Очищаем от всех пробельных символов в начале и конце
                line = line.strip()
                # Удаляем символы возврата каретки и другие невидимые символы
                line = line.replace('\r', '').replace('\n', '')
                
                if line and not line.startswith('#'):
                    # Убеждаемся, что ключ состоит из 3 частей
                    parts = line.split()
                    if len(parts) >= 2:  # минимум тип и ключ
                        # Сохраняем только тип и ключ (без комментария)
                        clean_key = f"{parts[0]} {parts[1]}"
                        keys.add(clean_key)
                        logger.debug(f"Очищенный ключ: {clean_key[:80]}...")
                    else:
                        logger.warning(f"Некорректный ключ: {line}")
        
        logger.info(f"✅ Загружено {len(keys)} ключей из {AUTHORIZED_KEYS_FILE}")
        
    except Exception as e:
        logger.error(f"Ошибка загрузки ключей: {e}")
    
    return keys

# ВАЖНО: ВЫЗЫВАЕМ функцию для загрузки ключей
AUTHORIZED_KEYS = load_authorized_keys()

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.channel = None
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_publickey(self, username, key):
        if username != SSH_USERNAME:
            return paramiko.AUTH_FAILED
        
        # Формируем строку ключа клиента
        client_key_string = f"{key.get_name()} {key.get_base64()}"
        
        # Очищаем от возможных пробельных символов
        client_key_string = client_key_string.strip()
        
        # Отладка с выводом длин и символов
        logger.info(f"🔑 Проверка ключа для {username}")
        logger.info(f"Ключ клиента: [{client_key_string}]")
        logger.info(f"Длина ключа клиента: {len(client_key_string)}")
        
        # Выводим каждый ключ из базы для сравнения
        for i, ak in enumerate(AUTHORIZED_KEYS):
            logger.info(f"Ключ из базы {i}: [{ak}]")
            logger.info(f"Длина ключа из базы: {len(ak)}")
            
            # Побайтовое сравнение
            if client_key_string == ak:
                logger.info("✅ Аутентификация УСПЕШНА!")
                return paramiko.AUTH_SUCCESSFUL
            else:
                # Находим разницу
                logger.debug(f"Ключи не совпадают")
    
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
    """Обработка команд робота"""
    print(f"📥 Получена команда: '{command}'")  # Отладка
    command = command.strip().lower()
    if len(command) > MAX_COMMAND_LENGTH:
        return "Ошибка: команда слишком длинная"
    
    func, response = COMMANDS.get(command, (None, f"Неизвестная команда: {command}"))
    if func:
        try:
            func()
            logger.info(f"Выполнена команда: {command}")
        except Exception as e:
            logger.error(f"Ошибка выполнения '{command}': {e}")
            return f"Ошибка: {str(e)}"
    return response

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
        
        # Основной цикл
        while True:
            channel.send("$ ".encode())
            
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
                
                response = handle_command(command)
                channel.send(f"{response}\r\n".encode())
                
            except socket.timeout:
                logger.warning("Таймаут ожидания команды")
                continue
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки: {e}")
                break
                
    except Exception as e:
        logger.error(f"Ошибка в SSH сессии: {e}", exc_info=True)
    finally:
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
    logger.info("=" * 50)
    logger.info("Запуск SSH сервера управления роботом")
    logger.info("=" * 50)
    
    # Проверяем существование файла с ключами
    if not os.path.exists(AUTHORIZED_KEYS_FILE):
        logger.error(f"❌ Файл не найден: {AUTHORIZED_KEYS_FILE}")
        logger.info("Создайте файл и добавьте публичные ключи:")
        logger.info(f"  mkdir -p /home/valli/.ssh")
        logger.info(f"  echo 'ssh-ed25519 ...' > {AUTHORIZED_KEYS_FILE}")
        logger.info(f"  chmod 600 {AUTHORIZED_KEYS_FILE}")
    
    start_ssh_server()