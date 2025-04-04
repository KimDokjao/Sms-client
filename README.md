# Sms-client
Этот проект представляет собой CLI-клиент для отправки SMS-сообщений через HTTP API. 

## Установка
1.  Клонируйте репозиторий:
   git clone <your_repository_url>
   cd <your_repository_directory>
2. Установите необходимые библиотеки: pip install toml

## Конфигурация
Создайте файл config.toml. Пример содержимого в файле config.toml

## Запуск
Запустите скрипт client.py с необходимыми аргументами: python client.py --config config.toml --sender "1234567890" --recipient "0987654321" --message "SMS"
Аргументы:
1. --config: Путь к файлу конфигурации TOML.
2. --sender: Номер отправителя.
3. --recipient: Номер получателя.
4. --message: Текст сообщения.

Информация о работе программы записывается в файл sms_client.log.

## Структура проекта
1. client.py: Основной файл скрипта.
2. config.toml: Пример файла конфигурации.
3. sms_client.log: Файл логов.
4. README.md: Этот файл.
