import re


def parse_yalex_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    let_pattern = r"let\s+(\w+)\s*=\s*(.+)"
    rule_pattern = r"rule\s+(\w+)\s*=\s*(.+)"

    lets = re.findall(let_pattern, content, re.MULTILINE)
    rules = re.findall(rule_pattern, content, re.MULTILINE | re.DOTALL)

    return lets, rules


def main():
    file_path = "yalex1.yal"
    lets, rules = parse_yalex_file(file_path)

    print("Lets:")
    for name, regex in lets:
        print(f"{name} = {regex}")

    print("\nRules:")
    for name, rule in rules:
        print(f"{name} = {rule}")


if __name__ == "__main__":
    main()
