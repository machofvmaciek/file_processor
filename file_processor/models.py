"""Text File Patcher."""

# Copyright 2025 by Maciej Olszewski
# https://github.com/machofvmaciek
# All rights reserved.

import logging

from decimal import Decimal
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator, model_serializer

_LOGGER = logging.getLogger("models.py")

DELIMITER = "\n"

# pylint: disable=no-member

class Header(BaseModel):
    """Represents Header in the Document/file."""
    __lengths = {
        "name": 28,
        "surname": 30,
        "patrynomic": 30,
        "address": 30,
    }

    field_id: str = Field(default="01", frozen=True)
    name: str = Field(min_length=1, max_length=__lengths["name"])
    surname: str = Field(min_length=1, max_length=__lengths["surname"])
    patrynomic: str = Field(min_length=1, max_length=__lengths["patrynomic"])
    address: str = Field(min_length=1, max_length=__lengths["address"])

    # pylint: disable=no-self-argument
    @field_validator("name", "surname", "patrynomic", "address")
    def sanitize_strings(cls, value: str) -> str:
        """Strip leading/trailing spaces and title the string."""
        return value.strip().title()

    @model_serializer
    def render(self) -> str:
        """Returns the specifically formatted string."""
        return (
            f"{self.field_id}"
            f"{self.name.rjust(self.__lengths['name'])}"
            f"{self.surname.rjust(self.__lengths['surname'])}"
            f"{self.patrynomic.rjust(self.__lengths['patrynomic'])}"
            f"{self.address.rjust(self.__lengths['address'])}"
            f"{DELIMITER}"
        )


class Currency(str, Enum):
    """Possible values for currency of the Transaction."""
    PLN = "PLN"
    EUR = "EUR"
    USD = "USD"


class Transaction(BaseModel):
    """Represents Transaction in the Document/file."""
    __lengths = {
        "counter": 6,
        "amount": 12,
        "currency": 3,
        "reserved": 97,
    }
    __counter_max = 20000

    field_id: str = Field(default="02", frozen=True)
    counter: int = Field(ge=1, le=__counter_max)
    amount: Decimal = Field(ge=0)
    currency: Currency = Field(min_length=1, max_length=__lengths["currency"])
    reserved: str = Field(default=" ", frozen=True)

    @field_validator("amount", mode="before")
    @classmethod
    def round_amount(cls, value: Decimal) -> Decimal:
        """Convert the decimal number to desired precision."""
        return round(value, 2)

    @staticmethod
    def amount_to_str(value: Decimal) -> str:
        """Converts Decimal type into string without a separator, always taking two decimal points."""
        return str(int(round(value, 2) * 100))

    @model_serializer
    def render(self) -> str:
        """Returns the specifically formatted string."""
        return (
            f"{self.field_id}"
            f"{str(self.counter).rjust(self.__lengths['counter'], '0')}"
            f"{self.amount_to_str(self.amount).rjust(self.__lengths['amount'], '0')}"
            f"{self.currency.rjust(self.__lengths['currency'])}"
            f"{self.__lengths['reserved'] * self.reserved}"
            f"{DELIMITER}"
        )


class Footer(BaseModel):
    """Represents Footer in the Document/file."""
    __lengths = {
        "total_counter": 6,
        "control_sum": 12,
        "reserved": 100,
    }

    field_id: str = Field(default="03", frozen=True)
    total_counter: int = Field(ge=1)
    control_sum: Decimal = Field(ge=0)
    reserved: str = Field(default=" ", frozen=True)

    @field_validator("control_sum", mode="before")
    @classmethod
    def round_amount(cls, value: Decimal) -> Decimal:
        """Convert the decimal number to desired precision."""
        return round(value, 2)

    @staticmethod
    def amount_to_str(value: Decimal) -> str:
        """Converts Decimal type into string without a separator, always taking two decimal points."""
        return str(int(round(value, 2) * 100))

    @model_serializer
    def render(self) -> str:
        """Returns the specifically formatted string."""
        return (
            f"{self.field_id}"
            f"{str(self.total_counter).rjust(self.__lengths['total_counter'], '0')}"
            f"{self.amount_to_str(self.control_sum).rjust(self.__lengths['control_sum'], '0')}"
            f"{self.__lengths['reserved'] * self.reserved}"
            f"{DELIMITER}"
        )


@dataclass
class Document:
    """Represents document constructed of Header, list of Transactions and a Footer."""

    header: Header
    transactions: list[Transaction]
    footer: Footer

# pylint: enable=no-member
