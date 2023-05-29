# Социальная сеть Yatube
Социальная сеть для публикации личных дневников
## Основные функции:
- Публикация постов;
- Поиск и подписка на любимых авторов;
- Комментирование публикаций.

## Используемый стек:
Python, Django, Pillow.

## Для запуска Вам понадобиться:
#### 1. Общие настройки:
- Клонировать репозиторий на ваш сервер:
```
git clone git@github.com:Pe4enka5/hw05_final.git
``` 
- Переходим в папку и устанавливаем виртуальное окружение 
```
python3 -m venv venv
source venv/Scripts/activate
``` 
- Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Выполнить миграции и создать после этого суперюзера
```
python manage.py migrate
python manage.py createsuperuser 
```
#### 2. Запуск приложения:
-Выполнить команду в папке с файлом manage.py
```
python manage.py runserver
```
Сервер работает, и вы можете пользоваться им!


### Автор: 
[Андрей Pe4enka Печерица](https://github.com/Pe4enka5)
Всем добра и печенек!
