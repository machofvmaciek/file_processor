"""Module implementing CLI for FileProcessor library."""

import logging

from typing_extensions import Annotated

from typer import Typer, Option, Argument

from file_processor.file_processor import FileProcessor, logging_init
from file_processor.models import Currency

_DEFAULT_DELIMITER = "\n"
_DEFAULT_LINE_LENGTH = 121
_DEFAULT_MAX_TRANSACTIONS = 20000

_LOGGER = logging.getLogger("main")

FILE_PROCESSOR_APP = Typer()

FILE_PROCESSOR_APP_UPDATE = Typer()
FILE_PROCESSOR_APP.add_typer(FILE_PROCESSOR_APP_UPDATE, name="update")


logging_init(file="testlog.log", level=logging.INFO)

# pylint: disable=too-many-arguments, too-many-positional-arguments

@FILE_PROCESSOR_APP.command()
def read(
    file: Annotated[str, Argument(help="File to read")],
    delimiter: Annotated[str, Option(help="Line delimiter used to read the file.")] = _DEFAULT_DELIMITER,
    line_length: Annotated[int, Option(help="Length of each line in given file.")] = _DEFAULT_LINE_LENGTH,
    max_transactions: Annotated[
        int, Option(help="Maxiumum number of allowed transactions in the file")
    ] = _DEFAULT_MAX_TRANSACTIONS,
) -> None:
    """Read given file."""
    _LOGGER.debug("file '%s'", file)
    _LOGGER.debug("delimiter '%s'", delimiter)
    _LOGGER.debug("line_length '%s'", line_length)
    _LOGGER.debug("max_transactions '%s'", max_transactions)

    processor = FileProcessor(delimiter, line_length, max_transactions)

    print(processor.read(file))


@FILE_PROCESSOR_APP.command()
def add(
    file: Annotated[str, Argument(help="File to read")],
    # Typer does not support Decimal type yet
    amount: Annotated[float, Argument(help="Amount of transaction to be added")],
    currency: Annotated[Currency, Argument(case_sensitive=False, help="Currency of transaction to be added")],
    delimiter: Annotated[str, Option(help="Line delimiter used to read the file.")] = _DEFAULT_DELIMITER,
    line_length: Annotated[int, Option(help="Length of each line in given file.")] = _DEFAULT_LINE_LENGTH,
    max_transactions: Annotated[
        int, Option(help="Maxiumum number of allowed transactions in the file")
    ] = _DEFAULT_MAX_TRANSACTIONS,
) -> None:
    """Add transaction to given file."""
    _LOGGER.debug("file '%s'", file)
    _LOGGER.debug("amount '%s'", amount)
    _LOGGER.debug("currency '%s'", currency)
    _LOGGER.debug("delimiter '%s'", delimiter)
    _LOGGER.debug("line_length '%s'", line_length)
    _LOGGER.debug("max_transactions '%s'", max_transactions)

    processor = FileProcessor(delimiter, line_length, max_transactions)
    processor.add_transaction(file, amount, currency)


@FILE_PROCESSOR_APP.command()
def delete(
    file: Annotated[str, Argument(help="File to read")],
    id: Annotated[int, Argument(help="ID of the transaction to delete.")],
    delimiter: Annotated[str, Option(help="Line delimiter used to read the file.")] = _DEFAULT_DELIMITER,
    line_length: Annotated[int, Option(help="Length of each line in given file.")] = _DEFAULT_LINE_LENGTH,
    max_transactions: Annotated[
        int, Option(help="Maxiumum number of allowed transactions in the file")
    ] = _DEFAULT_MAX_TRANSACTIONS,
) -> None:
    """Delete transaction from given file."""
    _LOGGER.debug("file '%s'", file)
    _LOGGER.debug("id '%s'", id)
    _LOGGER.debug("delimiter '%s'", delimiter)
    _LOGGER.debug("line_length '%s'", line_length)
    _LOGGER.debug("max_transactions '%s'", max_transactions)

    processor = FileProcessor(delimiter, line_length, max_transactions)
    processor.delete_transaction(file, id)


@FILE_PROCESSOR_APP_UPDATE.command(name="transaction")
def update_transaction(
    file: Annotated[str, Argument(help="File to read")],
    id: Annotated[int, Option(help="ID of the transaction to delete.")],
    # Typer does not support Decimal type yet
    amount: Annotated[float, Option("--amount", "-a", help="Amount of transaction to be added")],
    currency: Annotated[
        Currency, Option("--currency", "-c", case_sensitive=False, help="Currency of transaction to be added")
    ],
    delimiter: Annotated[str, Option(help="Line delimiter used to read the file.")] = _DEFAULT_DELIMITER,
    line_length: Annotated[int, Option(help="Length of each line in given file.")] = _DEFAULT_LINE_LENGTH,
    max_transactions: Annotated[
        int, Option(help="Maxiumum number of allowed transactions in the file")
    ] = _DEFAULT_MAX_TRANSACTIONS,
) -> None:
    """Update target transaction in given file."""
    _LOGGER.debug("file '%s'", file)
    _LOGGER.debug("id '%s'", id)
    _LOGGER.debug("amount '%s'", amount)
    _LOGGER.debug("currency '%s'", currency)
    _LOGGER.debug("delimiter '%s'", delimiter)
    _LOGGER.debug("line_length '%s'", line_length)
    _LOGGER.debug("max_transactions '%s'", max_transactions)

    processor = FileProcessor(delimiter, line_length, max_transactions)
    processor.update_transaction(file, id, amount, currency)


@FILE_PROCESSOR_APP_UPDATE.command(name="header")
def update_header(
    file: Annotated[str, Argument(help="File to read")],
    name: Annotated[str, Option(help="Name of the customer.")] = "",
    surname: Annotated[str, Option(help="Surname of the customer.")] = "",
    patrynomic: Annotated[str, Option(help="Patrynomic of the customer.")] = "",
    address: Annotated[str, Option(help="Address of the customer.")] = "",
    delimiter: Annotated[str, Option(help="Line delimiter used to read the file.")] = _DEFAULT_DELIMITER,
    line_length: Annotated[int, Option(help="Length of each line in given file.")] = _DEFAULT_LINE_LENGTH,
    max_transactions: Annotated[
        int, Option(help="Maxiumum number of allowed transactions in the file")
    ] = _DEFAULT_MAX_TRANSACTIONS,
) -> None:
    """Update header in given file."""
    _LOGGER.debug("file '%s'", file)
    _LOGGER.debug("id '%s'", id)
    _LOGGER.debug("name '%s'", name)
    _LOGGER.debug("surname '%s'", surname)
    _LOGGER.debug("patrynomic '%s'", patrynomic)
    _LOGGER.debug("address '%s'", address)
    _LOGGER.debug("delimiter '%s'", delimiter)
    _LOGGER.debug("line_length '%s'", line_length)
    _LOGGER.debug("max_transactions '%s'", max_transactions)

    processor = FileProcessor(delimiter, line_length, max_transactions)

    args = {}
    if name:
        args["name"] = name
    if surname:
        args["surname"] = surname
    if patrynomic:
        args["patrynomic"] = patrynomic
    if address:
        args["address"] = address

    processor.update_header(file, **args)


if __name__ == "__main__":
    FILE_PROCESSOR_APP()

# pylint: enable=too-many-arguments, too-many-positional-arguments
