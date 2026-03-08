from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = [
    "PatchBook",
    "IncomingBook",
    "ReturnedBook",
    "ReturnedAllBooks",
    "UpdateBook",
]


# Базовый класс "Книги", содержащий поля, которые есть во всех классах-наследниках.
class BaseBook(BaseModel):
    title: str
    author: str
    year: int
    seller_id: int


# Класс для обработки входных данных для частичного обновления данных о книге
class PatchBook(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int | None = None
    seller_id: int | None = None


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
class IncomingBook(BaseBook):
    pages: int = Field(
        default=100, alias="count_pages"
    )  # Пример использования тонкой настройки полей. Передачи в них метаинформации.

    @field_validator("year")  # Валидатор, проверяет что дата не слишком древняя
    @staticmethod
    def validate_year(val: int):
        if val < 2020:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val

    model_config = ConfigDict(populate_by_name=True)


class UpdateBook(BaseBook):
    pages: int

    @field_validator("year")
    @staticmethod
    def validate_year(val: int):
        if val < 2020:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedBook(BaseBook):  # {"id": 1, "title": "Clean Code", ....}
    id: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


# Класс для возврата массива объектов "Книга"
class ReturnedAllBooks(BaseModel):
    books: list[ReturnedBook]
