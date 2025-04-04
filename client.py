import argparse
import socket
import toml
import logging
import ssl
import json
import base64
from typing import Dict, Tuple

logging.basicConfig(filename='sms_client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class HTTPResponse:
    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes):
        self.status_code: int = status_code
        self.headers: Dict[str, str] = headers
        self.body: bytes = body

    @classmethod
    def from_bytes(cls, binary_data: bytes) -> "HTTPResponse":
        try:
            data: str = binary_data.decode()
            header_end: int = data.index("\r\n\r\n")
            header_data: str = data[:header_end]
            body: bytes = data[header_end + 4:].encode()

            header_lines: list[str] = header_data.split("\r\n")
            status_line: str = header_lines[0]
            status_code: int = int(status_line.split(" ")[1])

            headers: Dict[str, str] = {}
            for line in header_lines[1:]:
                if ":" in line:
                    key: str
                    value: str
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()

            return cls(status_code, headers, body)
        except Exception as e:
            logging.error(f"Ошибка при разборе ответа: {e}")
            return cls(500, {}, f'{{"error": "Ошибка парсинга: {e}"}}'.encode())

def send_sms(config: Dict[str, Dict[str, str]], sender: str, recipient: str, message: str) -> Tuple[int, str]:
    host: str = config["service"]["host"]
    port: int = config["service"]["port"]
    username: str = config["credentials"]["username"]
    password: str = config["credentials"]["password"]
    path: str = "/send_sms"  

    body_dict: Dict[str, str] = {"sender": sender, "recipient": recipient, "message": message}
    body: bytes = json.dumps(body_dict).encode()

    auth_string: bytes = f"{username}:{password}".encode()
    auth_header: str = base64.b64encode(auth_string).decode()

    headers: Dict[str, str] = {
        "Host": host,
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json",
        "Content-Length": str(len(body))
    }

    request: str = f"POST {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    for key, value in headers.items():
        request += f"{key}: {value}\r\n"
    request += "\r\n"
    request += body.decode()

    try:
        with socket.create_connection((host, port)) as sock:
            if config["service"].get("use_ssl", False):
                context: ssl.SSLContext = ssl.create_default_context()
                sock: socket.socket = context.wrap_socket(sock, server_hostname=host)

            sock.sendall(request.encode())

            response_bytes: bytes = b""
            while True:
                chunk: bytes = sock.recv(4096)
                if not chunk:
                    break
                response_bytes += chunk

        response: HTTPResponse = HTTPResponse.from_bytes(response_bytes)
        logging.info(f"Получен ответ: {response.status_code}, {response.body.decode()}")
        return response.status_code, response.body.decode()

    except Exception as e:
        logging.error(f"Ошибка при отправке запроса: {e}")
        return 500, str(e)

def main():
    parser = argparse.ArgumentParser(description="CLI клиент для отправки SMS.")
    parser.add_argument("--config", required=True, help="Путь к файлу конфигурации TOML.")
    parser.add_argument("--sender", required=True, help="Номер отправителя.")
    parser.add_argument("--recipient", required=True, help="Номер получателя.")
    parser.add_argument("--message", required=True, help="Текст сообщения.")

    args = parser.parse_args()

    try:
        config: Dict[str, Dict[str, str]] = toml.load(args.config)
        logging.info(f"Конфигурация загружена из {args.config}")
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        logging.error(f"Ошибка при загрузке конфигурации: {e}")
        return

    status_code: int
    body: str
    status_code, body = send_sms(config, args.sender, args.recipient, args.message)
    print(f"Код ответа: {status_code}")
    print(f"Тело ответа: {body}")

if __name__ == "__main__":
    main()
