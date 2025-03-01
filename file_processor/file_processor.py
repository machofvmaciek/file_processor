"""Module implements a FileProcessor class."""

import os
import logging

from decimal import Decimal
from typing import Optional, Union, IO
from pathlib import Path

from file_processor.models import Document, Header, Transaction, Footer

_LOGGER = logging.getLogger("file_processor")
logging.basicConfig(encoding="utf-8", level=logging.INFO)


def logging_init(file: str = None):
    # TODO
    pass


class ReadingException(Exception):
    """Custom Exception raised when could not read a file."""
    pass


class ValidationException(Exception):
    """Custom Exception raised when validation unsuccessful."""
    pass


class WriteException(Exception):
    """Custom Exception raised when file could not be written."""
    pass


class FileProcessor:
    """Functionalities to read, write and validate a specific text file format."""

    def __init__(self, delimiter: str = "\n", line_length: int = 121, max_transactions: int = 20000) -> None:
        """Initializes FileProcessor.

        Args:
            delimiter (str): End of line character.
            line_length (int): How long should the lines be.
            max_transactions (int): Maxiumum number of transactions allowed.
        """
        self.__delimiter = delimiter
        # 120 chars +1 for delimiter
        self.__line_length = line_length
        self.__max_transactions = max_transactions

    def __load_file_lines(self, path: str) -> list[str]:
        """Reads the plain text from given path and returns it in format of lines.

        Args:
            path (str): path to a file.

        Returns:
            List of strings, each containing a separate line of file, without leading and trailing whitespace chars.

        Raises:
            ValueError: When empty file was read.
        """
        _LOGGER.debug("Attempting to read '%s' file...", path)
        try:
            # Strip whitespace characters from the beginning and end of the file
            content = Path(path).read_text().strip()
            if not content:
                raise ValueError(f"File '{path} empty!")

            return content.split(self.__delimiter)

        except FileNotFoundError as exc:
            _LOGGER.critical("File '%s' not found!", path)
            raise ReadingException(f"Could not read '{path}' file!") from exc

    def __validate(self, lines: str) -> None:
        """Validates the read content.

        Args:
            lines (list[str]): text file content divided into lines.

        Raises:
            ValidationException: When validation failed.
        """
        _LOGGER.debug("Beginning validation...")

        for i, line in enumerate(lines):

            if len(line) > self.__line_length:
                _LOGGER.error("Line '%s' exceeds the length limit!", i)
                raise ValidationException(
                    f"Validation failed! Document exceeds maximum '{self.__line_length}' line limit!"
                )

        if not lines[0].startswith("01"):
            raise ValidationException("Validation failed! Invalid format of first row!")

        if not lines[-1].startswith("03"):
            raise ValidationException("Validation failed! Invalid format of last row!")

        # +2 for header and footer
        if len(lines) > self.__max_transactions + 2:
            raise ValidationException(
                "Validation failed! Exceeded maximum number of transactions ('%s').", self.__max_transactions
            )

        # Verify that all transactions between header and footer have '02' prefix
        if not any(x.startswith("02") for x in lines[1:-1]):
            raise ValidationException("Validation failed! Invalid format of a transaction!")

        _LOGGER.info("File validation successful!")

    def __get_document(self, lines: list[str]) -> Document:
        """Constructs a Document from given lines.

        Raises:
            ValidationException: When lines failed validation against document models.
        """
        _LOGGER.debug("Mapping file content into Document Models.")
        try:
            header_line = lines[0]
            header = Header(
                name=header_line[2:30],
                surname=header_line[30:60],
                patrynomic=header_line[60:90],
                address=header_line[90:120],
            )

            transactions = []

            for line in lines[1:-1]:
                transactions.append(
                    Transaction(
                        counter=line[2:8],
                        amount=float(int(line[8:20]) / 100),
                        currency=line[20:23],
                    )
                )

            footer_line = lines[-1]
            footer = Footer(
                total_counter=footer_line[2:8],
                control_sum=float(int(footer_line[8:20]) / 100),
            )
        except Exception as exc:
            _LOGGER.critical("Failed to construct a Document from given text file.")
            raise ValidationException from exc

        if transactions[-1].counter != footer.total_counter:
            raise ValidationException("Number of transactions and control sum form footer mismatch!")

        return Document(
            header=header,
            transactions=transactions,
            footer=footer,
        )

    @staticmethod
    def __create_footer(transactions: list[Transaction]) -> Footer:
        """Creates a footer based on given transactions."""
        control_sum = 0

        for transaction in transactions:
            control_sum += transaction.amount

        return Footer(total_counter=len(transactions), control_sum=control_sum)

    def read(self, file: str) -> str:
        """Read the contents of a file.

        Args:
            file (str): Path to file.

        Returns:
            str: File contents.

        Raises:
            ValueError: When empty path was provided.
        """
        if not file:
            raise ValueError("No file path provided.")

        lines = self.__load_file_lines(file)
        self.__validate(lines)

        return self.__get_document(lines)

    def __write_document_to_file(self, document: Document, file: str) -> None:
        """Writes the given document to a text file under specified path. Overwrites the file.

        Args:
            document (Document): Document which will be converted to a text file.
            file (str): Path to a file where document will be saved.
        """
        _LOGGER.debug("Attempting to write a '%s' file.", file)

        content = ""
        content += document.header.model_dump()

        for transaction in document.transactions:
            content += transaction.model_dump()

        content += document.footer.model_dump()

        if os.path.exists(file):
            _LOGGER.debug("Overwriting '%s' file!", file)

        Path(file).write_text(content)

    def update_transaction(self, file: str, id: int, amount: Decimal, currency: str) -> None:
        """Updates the given transaction in the file.

        Args:
            file (str): Path to file.
            id (int): ID of the transaction to modify
            amount (Decimal): new amount of transaction.
            currency (str): new currency of transaction.
        """
        # Check if given id is greater than zero and between accepted amount of transactions
        if id <= 0 or id > self.__max_transactions:
            raise ValueError(f"'id' must be in a range of [0, {self.__max_transactions})! Got '{id}'.")

        document = self.read(file)

        # Chek if given id is present in the document
        if id > document.footer.total_counter:
            raise ValueError("'id' not present in the file!")

        new = Transaction(counter=id, amount=amount, currency=currency.upper())

        target_transaction = document.transactions[id - 1]

        if target_transaction.currency != new.currency:
            _LOGGER.warning(
                "Changing the currency of transaction with id = '%s' from '%s' to '%s'",
                id,
                target_transaction.currency,
                new.currency,
            )

        document.transactions[id - 1] = new

        # Update footer to match new transaction
        document.footer = self.__create_footer(document.transactions)

        self.__write_document_to_file(document, file)
        _LOGGER.info("Successfully updated transaction with id = '%s'.", id)

    def update_header(self, file: str, **kwargs) -> None:
        """Updates the data stored in a header.
        Args:
            file (str): Path to file.

        Keyword args:
            name (str): name of the client.
            surname (str): surname of the client.
            patrynomic (str): patrynomic of the client.
            address (str): address of the client.
        """
        attribute_to_value_mapper = {
            "name": kwargs.get("name", ""),
            "surname": kwargs.get("surname", ""),
            "patrynomic": kwargs.get("patrynomic", ""),
            "address": kwargs.get("address", ""),
        }

        if not any(attribute_to_value_mapper.values()):
            _LOGGER.debug("Data to update header not provided.")
            return

        # Load the document and update it
        document = self.read(file)
        for key, value in attribute_to_value_mapper.items():
            if value:
                setattr(document.header, key, value)

        self.__write_document_to_file(document, file)
        _LOGGER.info("Successfully updated the header of '%s' file!", file)

    def add_transaction(self, file: str, amount: Decimal, currency: str) -> None:
        """Adds transaction to the file based on given amount and currency. Automatically calculates the index
        of transaction. Updates the footer. Check if maxiumum number of transactions was not exceeded.

        Args:
            file (str): Path to file.
            amount (Decimal): amount of transaction.
            currency (str): currency of transaction.
        """
        document = self.read(file)

        if document.footer.total_counter == self.__max_transactions:
            raise WriteException(f"Addition failed! Exceeded maximum of '{self.__max_transactions}' transactions.")

        new = Transaction(
            counter=document.footer.total_counter + 1,
            amount=amount,
            currency=currency.upper(),
        )
        document.transactions.append(new)

        # Update the footer to match new amount of transactions
        document.footer = self.__create_footer(document.transactions)

        self.__write_document_to_file(document, file)
        _LOGGER.info("Successfully updated '%s' file!", file)

    def delete_transaction(self, file: str, id: int) -> None:
        """Deletes the transaction with given id. Decrements all the following transactions's ids.
        Args:
            file (str): Path to file.
            id (int): id of transaction to delete.
        """
        document = self.read(file)

        if id <= 0 or id > document.footer.total_counter:
            raise ValueError(f"'id' must be in a range of [0, {document.footer.total_counter})! Got '{id}'.")

        # Delete the selected transaction
        _LOGGER.debug("Deleting the transaction: '%s'", document.transactions[id - 1])
        document.transactions.pop(id - 1)

        # Decrement the ids of all transactions after selected
        for transaction in document.transactions[id - 1 :]:
            transaction.counter -= 1

        document.footer = self.__create_footer(document.transactions)

        self.__write_document_to_file(document, file)
        _LOGGER.info("Successfully updated '%s' file!", file)

    def create(self, file: str, header: Header, transactions: list[Transaction]) -> None:
        """Create a file based on given header and list of transactions. The footer is created automatically.

        Args:
            file (str): Path to file.
            header (Header): Header object containing information about the customer.
            transactions (list[Transaction]): list containing all transactions.
        """

        document = Document(
            header=header,
            transactions=transactions,
            footer=self.__create_footer(transactions),
        )

        if os.path.exists(file):
            _LOGGER.debug("Overwirting '%s' file!", file)

        self.__write_document_to_file(document, file)
