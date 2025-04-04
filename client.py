import argparse
import socket
import toml
import logging
import ssl
import json
import base64

logging.basicConfig(filename='sms_client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class HTTPResponse:
    def __init__(self, status_code, headers, body):
        self.status_code = status_code
        self.headers = headers
        self.body = body

    @classmethod
    def from_bytes(cls, binary_data: bytes):
        try:
            data = binary_data.decode()
            header_end = data.index("\r\n\r\n")
            header_data = data[:header_end]
            body = data[header_end + 4:].encode()

            header_lines = header_data.split("\r\n")
            status_line = header_lines[0]
            status_code = int(status_line.split(" ")[1])

            headers = {}
            for line in header_lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()

            return cls(status_code, headers, body)
        except Exception as e:
            logging.error(f"Ошибка при парсинге ответа: {e}")
            return cls(500, {}, b"Error parsing response")

def send_sms(config, sender, recipient, message):
    host = config["service"]["host"]
    port = config["service"]["port"]
    username = config["credentials"]["username"]
    password = config["credentials"]["password"]
    path = "/send_sms"  

    body_dict = {"sender": sender, "recipient": recipient, "message": message}
    body = json.dumps(body_dict).encode()

    auth_string = f"{username}:{password}".encode()
    auth_header = base64.b64encode(auth_string).decode()

    headers = {
        "Host": host,
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json",
        "Content-Length": str(len(body))
    }

    request = f"POST {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    for key, value in headers.items():
        request += f"{key}: {value}\r\n"
    request += "\r\n"
    request += body.decode()

    try:
        with socket.create_connection((host, port)) as sock:
            if config["service"].get("use_ssl", False):
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)

            sock.sendall(request.encode())

            response_bytes = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_bytes += chunk

        response = HTTPResponse.from_bytes(response_bytes)
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
        config = toml.load(args.config)
        logging.info(f"Конфигурация загружена из {args.config}")
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        logging.error(f"Ошибка при загрузке конфигурации: {e}")
        return

    status_code, body = send_sms(config, args.sender, args.recipient, args.message)
    print(f"Код ответа: {status_code}")
    print(f"Тело ответа: {body}")

if __name__ == "__main__":
    main()
