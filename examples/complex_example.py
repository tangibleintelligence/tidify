import json

from tidify import tidify
from tabulate import tabulate


def main():
    with open("complex_example.json", "r") as f:
        data = json.load(f)

    df = tidify(data, exclude=["languages", "pets.age"])
    print(
        tabulate(
            df,
            headers="keys",
            tablefmt="grid",
        )
    )


if __name__ == "__main__":
    main()
