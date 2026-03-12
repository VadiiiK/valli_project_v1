import paramiko
import socket
import threading


# Настройки SSH
SSH_HOST = '0.0.0.0'
SSH_PORT = 2222
SSH_USERNAME = 'valli'

# Пути к ключам
HOST_KEY_FILE_ED25519 = 'ssh_host_ed25519_key'
HOST_KEY_FILE_RSA = 'ssh_host_rsa_key'  # запасной вариант
AUTHORIZED_KEYS_FILE = '/home/valli/.ssh/authorized_keys'

# Константы
MAX_COMMAND_LENGTH = 100
MAX_CLIENTS = 50
SESSION_TIMEOUT = 300  # 5 минут

# Загружаем авторизованные ключи при старте
def load_authorized_keys():
    try:
        with open(AUTHORIZED_KEYS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"Файл авторизованных ключей не найден: {AUTHORIZED_KEYS_FILE}")
        return set()
    except Exception as e:
        print(f"Ошибка чтения файла ключей: {e}")
        return set()

AUTHORIZED_KEYS = str(load_authorized_keys())

class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        if username != SSH_USERNAME:
            print(f"Неверный пользователь: {username}")
            return paramiko.AUTH_FAILED

        client_key_string = f"{key.get_name()} {key.get_base64()}"
        # print(type(client_key_string))
        # print(type(AUTHORIZED_KEYS))
        if client_key_string in AUTHORIZED_KEYS:
            print(f"Успешная аутентификация по ключу для пользователя {username}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            print(f"Ключ не авторизован для пользователя {username}: {client_key_string[:50]}...")
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    

def test_ssh_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((SSH_HOST, SSH_PORT))
    sock.listen(5)
    print(f"Тестовый сервер запущен на {SSH_HOST}:{SSH_PORT}")

    while True:
        client, addr = sock.accept()
        print(f"Подключение от {addr}")
        try:
            transport = paramiko.Transport(client)
            key = paramiko.RSAKey.generate(2048)
            transport.add_server_key(key)
            server = SSHServer()
            transport.start_server(server=server)
            print("Транспорт запущен")
        except Exception as e:
            print(f"Ошибка: {e}")
            client.close()

if __name__ == "__main__":
    test_ssh_server()