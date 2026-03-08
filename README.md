# Book Marketplace API

Учебное FastAPI-приложение для объявлений о продаже книг.

Реализовано:

- CRUD для книг
- CRUD для продавцов
- связь `Seller 1 -> N Book`
- `seller_id` в ответах book-эндпоинтов
- каскадное удаление книг при удалении продавца
- JWT-авторизация
- хеширование паролей через `bcrypt`
- валидация email через `EmailStr`
- тесты на обязательные и дополнительные эндпоинты

## Стек

- FastAPI
- SQLAlchemy Async
- PostgreSQL
- Docker Compose
- Pytest

## Запуск в Docker

1. Из корня проекта выполнить:

```bash
docker compose -p mts_books_market up -d --build
```

2. Приложение будет доступно по адресу:

```text
http://localhost:18017
```

3. Swagger:

```text
http://localhost:18017/docs
```

4. PostgreSQL проброшен на нестандартный внешний порт:

```text
55439
```

## Переменные окружения

Используется файл `.env`.

Основные переменные:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USERNAME`
- `DB_PASSWORD`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRATION_MINUTES`

## Тесты

Прогон тестов внутри контейнера приложения:

```bash
docker compose -p mts_books_market exec app pytest -q
```

Текущее состояние:

```text
22 passed
```

## Ручная проверка

Файл с готовыми запросами:

```text
api_tests.http
```

Он рассчитан на запуск приложения на `http://localhost:18017`.

## Эндпоинты

### Books

- `GET /api/v1/books/`
- `POST /api/v1/books/`
- `GET /api/v1/books/{book_id}`
- `PUT /api/v1/books/{book_id}`
- `PATCH /api/v1/books/{book_id}`
- `DELETE /api/v1/books/{book_id}`

### Sellers

- `POST /api/v1/seller`
- `GET /api/v1/seller`
- `GET /api/v1/seller/{seller_id}`
- `PUT /api/v1/seller/{seller_id}`
- `DELETE /api/v1/seller/{seller_id}`

### Auth

- `POST /api/v1/token`

## JWT

Токен передаётся в заголовке:

```text
Authorization: Bearer <token>
```

Защищены эндпоинты:

- `GET /api/v1/seller/{seller_id}`
- `PUT /api/v1/seller/{seller_id}`
- `DELETE /api/v1/seller/{seller_id}`
- `POST /api/v1/books/`
- `PUT /api/v1/books/{book_id}`

Дополнительно защищён:

- `PATCH /api/v1/books/{book_id}`
