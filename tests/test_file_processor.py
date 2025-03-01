"""Unit testing the file_processor.py functionalities."""

import copy

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from file_processor.file_processor import FileProcessor, ReadingException, ValidationException, WriteException
from file_processor.models import Header, Transaction, Footer, Document, Currency

_TEST_FILE_1_TRANSACTION = """
01                        John                           Doe                         Smith               123 Main Street
02000001000000000100USD                                                                                                 
03000001000000000100                                                                                                    
"""

_TEST_FILE_1_TRANSACTION_LINES = [
    "01                        John                           Doe                         Smith               123 Main Street",
    "02000001000000000100USD                                                                                                 ",
    "03000001000000000100",
]

_TEST_FILE_1_TRANSACTION_LINES_TOO_LONG = _TEST_FILE_1_TRANSACTION_LINES + [122 * "-"]
_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_HEADER = [121 * "-"] + _TEST_FILE_1_TRANSACTION_LINES[1:]
_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_FOOTER = _TEST_FILE_1_TRANSACTION_LINES[:2] + [121 * "-"]
_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_TRANSACTION = (
    _TEST_FILE_1_TRANSACTION_LINES[:1] + [121 * "-"] + _TEST_FILE_1_TRANSACTION_LINES[2:]
)

_TEST_FILE_1_TRANSACTION_DOCUMENT = Document(
    header=Header(field_id="01", name="John", surname="Doe", patrynomic="Smith", address="123 Main Street"),
    transactions=[Transaction(field_id="02", counter=1, amount=Decimal("1.0"), currency=Currency.USD, reserved=" ")],
    footer=Footer(field_id="03", total_counter=1, control_sum=Decimal("1.0"), reserved=" "),
)

_TEST_FOOTER_MAX_TRANSACTIONS_DOCUMENT = Document(
    header=Header(field_id="01", name="John", surname="Doe", patrynomic="Smith", address="123 Main Street"),
    transactions=[],
    footer=Footer(field_id="03", total_counter=20000, control_sum=Decimal("1.0"), reserved=" "),
)

_TEST_2_TRANSACTIONS_DOCUMENT = Document(
    header=Header(field_id="01", name="John", surname="Doe", patrynomic="Smith", address="123 Main Street"),
    transactions=[
        Transaction(field_id="02", counter=1, amount=Decimal("1.0"), currency=Currency.USD, reserved=" "),
        Transaction(field_id="02", counter=2, amount=Decimal("2.0"), currency=Currency.USD, reserved=" "),
    ],
    footer=Footer(field_id="03", total_counter=2, control_sum=Decimal("3.0"), reserved=" "),
)


class TestFileProcessor:
    """Unit testing the FileProcessor."""

    @pytest.fixture
    def processor(self) -> FileProcessor:
        return FileProcessor()

    def get_document_copy(document: Document) -> Document:
        """Returns a deepcopy of given document, so that the mocks dont overwrite the original objects."""
        return copy.deepcopy(document)

    @staticmethod
    def get_processor(delimiter: str = "\n", line_length: int = 121, max_transactions: int = 20000) -> FileProcessor:
        return FileProcessor(delimiter, line_length, max_transactions)

    @staticmethod
    def test_read_empty_path(processor: FileProcessor) -> None:
        # Act & Assert
        with pytest.raises(ValueError):
            processor.read("")

    @staticmethod
    def test_read_load_file_lines_empty_file(processor: FileProcessor) -> None:
        # Act & Assert
        with pytest.raises(ValueError):
            with patch("pathlib.Path.read_text", return_value=""):
                processor.read("foo.txt")

    @staticmethod
    def test_read_load_file_lines_file_missing(processor: FileProcessor) -> None:
        # Act & Assert
        with pytest.raises(ReadingException):
            with patch("pathlib.Path.read_text", side_effect=FileNotFoundError()):
                processor.read("foo.txt")

    @staticmethod
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__validate")
    def test_read_load_file_lines_success(mock_validate: Mock, processor: FileProcessor) -> None:
        # Act
        with patch("pathlib.Path.read_text", return_value=_TEST_FILE_1_TRANSACTION):
            processor.read("foo.txt")

        # Assert
        mock_validate.assert_called_once_with(_TEST_FILE_1_TRANSACTION_LINES)

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor._FileProcessor__load_file_lines",
        Mock(return_value=_TEST_FILE_1_TRANSACTION_LINES),
    )
    def test_read_validate_success(processor: FileProcessor) -> None:
        # Act & Assert
        processor.read("foo.txt")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor._FileProcessor__load_file_lines",
        Mock(return_value=_TEST_FILE_1_TRANSACTION_LINES_TOO_LONG),
    )
    def test_read_validate_line_too_long(processor: FileProcessor) -> None:
        # Act & Assert
        with pytest.raises(ValidationException):
            processor.read("foo.txt")

    @staticmethod
    @pytest.mark.parametrize(
        "lines",
        [
            (_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_HEADER),
            (_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_FOOTER),
            (_TEST_FILE_1_TRANSACTION_LINES_INCORRECT_TRANSACTION),
        ],
    )
    def test_read_validate_incorrect_ids(processor: FileProcessor, lines: list[str]) -> None:
        # Act & Assert
        with patch(
            "file_processor.file_processor.FileProcessor._FileProcessor__load_file_lines", Mock(return_value=lines)
        ):
            with pytest.raises(ValidationException):
                processor.read("foo.txt")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor._FileProcessor__load_file_lines",
        Mock(return_value=_TEST_FILE_1_TRANSACTION_LINES),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__validate", Mock())
    def test_read_get_document_success(processor: FileProcessor) -> None:
        document = processor.read("foo.txt")

        assert document == _TEST_FILE_1_TRANSACTION_DOCUMENT

    @staticmethod
    @pytest.mark.parametrize("id", [(0), (20001), (2)])
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_FILE_1_TRANSACTION_DOCUMENT)),
    )
    def test_update_transaction_wrong_id(processor: FileProcessor, id: int) -> None:
        # Act & Assert
        with pytest.raises(ValueError):
            processor.update_transaction("foo.txt", id, 0, "USD")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_FILE_1_TRANSACTION_DOCUMENT)),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_update_transaction_success(mock_write_document: Mock, processor: FileProcessor) -> None:
        # Arrange
        id = 1
        amount = 5
        currency = "USD"

        expected_document = Document(
            header=copy.deepcopy(_TEST_FILE_1_TRANSACTION_DOCUMENT.header),
            transactions=[
                Transaction(field_id="02", counter=1, amount=Decimal("5.0"), currency=Currency.USD, reserved=" ")
            ],
            footer=Footer(field_id="03", total_counter=1, control_sum=Decimal("5.0"), reserved=" "),
        )

        # Act
        processor.update_transaction("foo.txt", id, amount, currency)

        # Assert
        mock_write_document.assert_called_once_with(expected_document, "foo.txt")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_FILE_1_TRANSACTION_DOCUMENT)),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    @pytest.mark.parametrize(
        "kwargs, expected_header",
        [
            (
                {"name": "Lucifer", "surname": "Morningstar"},
                Header(name="Lucifer", surname="Morningstar", patrynomic="Smith", address="123 Main Street"),
            ),
            (
                {"name": "Lucifer", "surname": "Morningstar", "patrynomic": "The Devil", "address": "Lux, Los Angeles"},
                Header(name="Lucifer", surname="Morningstar", patrynomic="The Devil", address="Lux, Los Angeles"),
            ),
        ],
    )
    def test_update_header_success(
        mock_write_document: Mock, processor: FileProcessor, kwargs: dict[str, str], expected_header: Header
    ) -> None:
        # Arrange
        expected_document = Document(
            expected_header,
            copy.deepcopy(_TEST_FILE_1_TRANSACTION_DOCUMENT.transactions),
            copy.deepcopy(_TEST_FILE_1_TRANSACTION_DOCUMENT.footer),
        )

        # Act
        processor.update_header("foo.txt", **kwargs)

        # Assert
        mock_write_document.assert_called_once_with(expected_document, "foo.txt")

    @staticmethod
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_update_header_empty_kwargs(mock_write_document: Mock, processor: FileProcessor) -> None:
        # Act
        processor.update_header("foo.txt", **{})

        # Assert
        mock_write_document.assert_not_called()

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_FOOTER_MAX_TRANSACTIONS_DOCUMENT)),
    )
    def test_add_transaction_exceeded_max(processor: FileProcessor) -> None:
        # Act & Assert
        with pytest.raises(WriteException):
            processor.add_transaction("foo.txt", 1, "USD")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_2_TRANSACTIONS_DOCUMENT)),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_add_transaction_success(mock_write_document: Mock, processor: FileProcessor) -> None:
        # Arrange
        amount = Decimal(3)
        currency = "USD"

        # Create a copy of the entry document
        expected_document = copy.deepcopy(_TEST_2_TRANSACTIONS_DOCUMENT)
        expected_document.transactions.append(Transaction(counter=3, amount=amount, currency=currency))
        expected_document.footer = Footer(total_counter=3, control_sum=Decimal(6))

        # Act
        processor.add_transaction("foo.txt", amount, currency)

        # Assert
        mock_write_document.assert_called_once_with(expected_document, "foo.txt")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_2_TRANSACTIONS_DOCUMENT)),
    )
    @pytest.mark.parametrize("id", [(0), (3)])
    def test_delete_transaction_wrong_id(processor: FileProcessor, id: int) -> None:
        # Act & Assert
        with pytest.raises(ValueError):
            processor.delete_transaction("foo.txt", id)

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_2_TRANSACTIONS_DOCUMENT)),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_delete_transaction_success_last_transaction(mock_write_document: Mock, processor: FileProcessor) -> None:
        # Arrange
        # Create a copy of the entry document
        expected_document = copy.deepcopy(_TEST_2_TRANSACTIONS_DOCUMENT)

        # Delete last transaction
        expected_document.transactions.pop()

        # Update the footer
        expected_document.footer = Footer(total_counter=1, control_sum=Decimal(1))

        # Act
        processor.delete_transaction("foo.txt", 2)

        # Assert
        mock_write_document.assert_called_once_with(expected_document, "foo.txt")

    @staticmethod
    @patch(
        "file_processor.file_processor.FileProcessor.read",
        Mock(return_value=get_document_copy(_TEST_2_TRANSACTIONS_DOCUMENT)),
    )
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_delete_transaction_success_middle_transaction(mock_write_document: Mock, processor: FileProcessor) -> None:
        """
        This test verifies if the middle transaction is deleted, the following ones have updated counters.
        For purpose of the easy testing, first transaction will be deleted, as from business perspective of the method
        behaviour should be the same.
        """
        # Arrange
        # Create a copy of the entry document
        expected_document = copy.deepcopy(_TEST_2_TRANSACTIONS_DOCUMENT)

        # Delete first(middle-like) transaction
        expected_document.transactions.pop(0)

        # Update the counter of the left transaction
        expected_document.transactions[0].counter = 1

        # Update the footer
        expected_document.footer = Footer(total_counter=1, control_sum=Decimal(2))

        # Act
        processor.delete_transaction("foo.txt", 1)

        # Assert
        mock_write_document.assert_called_once_with(expected_document, "foo.txt")

    @staticmethod
    @patch("file_processor.file_processor.FileProcessor._FileProcessor__write_document_to_file")
    def test_create(mock_write_document: Mock, processor: FileProcessor) -> None:
        # Act
        processor.create(
            "foo.txt", _TEST_FILE_1_TRANSACTION_DOCUMENT.header, _TEST_FILE_1_TRANSACTION_DOCUMENT.transactions
        )

        # Assert
        mock_write_document.assert_called_once_with(_TEST_FILE_1_TRANSACTION_DOCUMENT, "foo.txt")
