"""Unit-testing the models."""

from decimal import Decimal

import pytest

from pydantic import ValidationError

from file_processor.models import Header, Transaction, Footer


class TestHeader:
    """Unit-testing the Header."""

    name = "Lucifer"
    surname = "Mornigstar"
    patrynomic = "The Devil"
    address = "Lux, Los Angeles"

    def get_header() -> Header:
        return Header(
            name=TestHeader.name,
            surname=TestHeader.surname,
            patrynomic=TestHeader.patrynomic,
            address=TestHeader.address,
        )

    @staticmethod
    def test_init_field_id_defaut_value_success() -> None:
        # Arrange & Act
        header = TestHeader.get_header()

        assert header.field_id == "01"

    @staticmethod
    def test_field_id_frozen() -> None:
        # Arrange
        header = TestHeader.get_header()

        # Act & Assert
        with pytest.raises(ValidationError):
            header.field_id = "new_id"

    @staticmethod
    def test_init_fields_min_length() -> None:
        # Act & Assert
        with pytest.raises(ValidationError):
            Header(name="", surname="", patrynomic="", address="")

    @staticmethod
    def test_init_fields_max_length() -> None:
        # Act & Assert
        with pytest.raises(ValidationError):
            Header(name=29 * "a", surname="", patrynomic="", address="")

    @staticmethod
    def test_sanitize_strings_success() -> None:
        # Arrange & Act
        name = "Lucifer"
        surname = "Mornigstar"
        header = Header(
            name=f"  {TestHeader.name}",
            surname=f"  {TestHeader.surname}   ",
            patrynomic=TestHeader.patrynomic,
            address=TestHeader.address,
        )

        # Assert
        assert header.name == name
        assert header.surname == surname

    @staticmethod
    def test_model_dump_render_success() -> None:
        # Arrange
        header = TestHeader.get_header()

        # Act
        result = header.model_dump()

        # Assert
        assert len(result) == 121
        assert "01" in result

        assert TestHeader.name in result
        assert TestHeader.surname in result
        assert TestHeader.patrynomic in result
        assert TestHeader.address in result

        assert "\n" in result


class TestTransaction:
    """Unit-testing the Transaction"""

    counter = 1
    amount = 10.50
    amount_converted = "1050"
    currency = "PLN"

    @staticmethod
    def get_transaction() -> Transaction:
        return Transaction(
            counter=TestTransaction.counter,
            amount=TestTransaction.amount,
            currency=TestTransaction.currency,
        )

    @staticmethod
    def test_init_field_id_defaut_value_success() -> None:
        # Arrange & Act
        transaction = TestTransaction.get_transaction()

        assert transaction.field_id == "02"

    @staticmethod
    def test_field_id_frozen() -> None:
        # Arrange
        transaction = TestTransaction.get_transaction()

        # Act & Assert
        with pytest.raises(ValidationError):
            transaction.field_id = "new_id"

    @staticmethod
    def test_init_min_max_values() -> None:
        # Act & Assert
        # All values in range
        Transaction(counter=TestTransaction.counter, amount=TestTransaction.amount, currency=TestTransaction.currency)

        # Counter below minimum
        with pytest.raises(ValidationError):
            Transaction(counter=-10, amount=TestTransaction.amount, currency=TestTransaction.currency)

        # Counter over maxiumum
        with pytest.raises(ValidationError):
            Transaction(counter=20001, amount=TestTransaction.amount, currency=TestTransaction.currency)

        # Amount below minimum
        with pytest.raises(ValidationError):
            Transaction(counter=TestTransaction.counter, amount=-1, currency=TestTransaction.currency)

    @staticmethod
    @pytest.mark.parametrize(
        "currency,success",
        [
            ("PLN", True),
            ("USD", True),
            ("EUR", True),
            ("not_supported", False),
        ],
    )
    def test_init_currency_supported(currency: str, success: bool) -> None:
        # Act & Assert
        if success:
            Transaction(counter=TestTransaction.counter, amount=TestTransaction.amount, currency=currency)
        else:
            with pytest.raises(ValidationError):
                Transaction(counter=TestTransaction.counter, amount=TestTransaction.amount, currency=currency)

    @staticmethod
    @pytest.mark.parametrize(
        "amount,expected",
        [
            (5.1, Decimal(5.1)),
            (5.11, Decimal(5.11)),
            (5.111, Decimal(5.11)),
            (5.16, Decimal(5.20)),
        ],
    )
    def test_round_amount(amount: float, expected: Decimal) -> None:
        # Act
        transaction = Transaction(counter=TestTransaction.counter, amount=amount, currency=TestTransaction.currency)

        assert transaction.amount.compare(expected)

    @staticmethod
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal(5), "500"),
            (Decimal(5.1), "510"),
            (Decimal(5.11), "511"),
            (Decimal(5.111), "511"),
        ],
    )
    @staticmethod
    def test_amount_to_str(value: Decimal, expected: str) -> None:
        # Arrange
        transaction = TestTransaction.get_transaction()

        # Act & Assert
        assert transaction.amount_to_str(value) == expected

    @staticmethod
    def test_model_dump_render() -> None:
        # Arrange
        transaction = TestTransaction.get_transaction()
        whitespaces = 97 * (" ")

        # Act
        result = transaction.model_dump()

        # Assert
        assert len(result) == 121
        assert "02" in result

        assert str(TestTransaction.counter) in result
        assert TestTransaction.amount_converted in result
        assert str(TestTransaction.currency) in result

        assert whitespaces in result
        assert "\n" in result


class TestFooter:
    """Unit-testing the footer class."""

    total_counter = 10
    control_sum = 50.20
    control_sum_converted = "5020"

    @staticmethod
    def get_footer() -> Footer:
        return Footer(total_counter=TestFooter.total_counter, control_sum=TestFooter.control_sum)

    @staticmethod
    def test_init_field_id_defaut_value_success() -> None:
        # Arrange & Act
        footer = TestFooter.get_footer()

        assert footer.field_id == "03"

    @staticmethod
    def test_field_id_frozen() -> None:
        # Arrange
        footer = TestFooter.get_footer()

        # Act & Assert
        with pytest.raises(ValidationError):
            footer.field_id = "new_id"

    @staticmethod
    def test_init_min_max_values() -> None:
        # Act & Assert
        # All values in range
        Footer(total_counter=TestFooter.total_counter, control_sum=TestFooter.control_sum)

        # Counter below minimum
        with pytest.raises(ValidationError):
            Footer(total_counter=0, control_sum=TestFooter.control_sum)

        # total_counter below minimum
        with pytest.raises(ValidationError):
            Footer(total_counter=TestFooter.total_counter, control_sum=-1)

    @staticmethod
    @pytest.mark.parametrize(
        "amount,expected",
        [
            (5.1, Decimal(5.1)),
            (5.11, Decimal(5.11)),
            (5.111, Decimal(5.11)),
            (5.16, Decimal(5.20)),
        ],
    )
    def test_round_amount(amount: float, expected: Decimal) -> None:
        # Act
        footer = Footer(total_counter=TestFooter.total_counter, control_sum=amount)

        assert footer.control_sum.compare(expected)

    @staticmethod
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal(5), "500"),
            (Decimal(5.1), "510"),
            (Decimal(5.11), "511"),
            (Decimal(5.111), "511"),
        ],
    )
    @staticmethod
    def test_amount_to_str(value: Decimal, expected: str) -> None:
        # Arrange
        footer = TestFooter.get_footer()

        # Act & Assert
        assert footer.amount_to_str(value) == expected

    @staticmethod
    def test_model_dump_render() -> None:
        # Arrange
        footer = TestFooter.get_footer()
        whitespaces = 100 * (" ")

        # Act
        result = footer.model_dump()

        # Assert
        assert len(result) == 121
        assert "03" in result
        assert str(TestFooter.total_counter) in result
        assert TestFooter.control_sum_converted in result

        assert whitespaces in result
        assert "\n" in result
