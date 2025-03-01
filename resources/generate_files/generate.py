import os

def pad_left(value: str, length: int) -> str:
    """
    Pad the given value with leading spaces to match the required length.
    """
    return value.rjust(length)

def generate_fixed_width_file(filename: str, num_transactions: int = 10):
    """
    Generate a fixed-width formatted file according to the specified format.

    Args:
        filename (str): The name of the output file.
        num_transactions (int): Number of transactions to include.
    """
    header = (
        pad_left("01", 2) +
        pad_left("John", 28) +
        pad_left("Doe", 30) +
        pad_left("Smith", 30) +
        pad_left("123 Main Street", 30) + "\n"
    )
    
    transactions = ""
    total_amount = 0
    for i in range(1, num_transactions + 1):
        amount = i * 100  # Example: 1.00, 2.00, ..., 10.00 (stored as cents)
        total_amount += amount
        transactions += (
            pad_left("02", 2) +
            pad_left(f"{i:06}", 6) +
            pad_left(f"{amount:012}", 12) +
            pad_left("USD", 3) +
            pad_left("", 97) + "\n"
        )
    
    footer = (
        pad_left("03", 2) +
        pad_left(f"{num_transactions:06}", 6) +
        pad_left(f"{total_amount:012}", 12) +
        pad_left("", 101) + "\n"
    )
    
    with open(filename, "w", newline="\n") as file:
        file.write(header + transactions + footer)
    
    print(f"File '{filename}' generated successfully with {num_transactions} transactions.")

if __name__ == "__main__":
    generate_fixed_width_file(os.path.join("txts", "file_1_trans.txt"), num_transactions=1)
    # print("aaa".rjust(20))
