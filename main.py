import re
from graphviz import Digraph


class Token:
    def __init__(self, name, regex):
        self.name = name
        self.regex = regex


TOKENS = [
    Token("Identificador", r"\b[a-zA-Z_]\w*\b"),
    Token("Operador de suma", r"\+"),
    Token("Operador de resta", r"-"),
    Token("Operador de multiplicación", r"\*"),
    Token("Operador de asignación", r"="),
    Token("Número", r"\b\d+(\.\d+)?\b"),
    Token("Comentario", r"/\*.*?\*/"),
    Token("String", r'"(?:[^"\\]|\\.)*"'),
    Token("Let", r"\blet\b"),
    Token("Rule", r"\brule\b"),
    Token("Or", r"\|"),
    Token("LParen", r"\("),
    Token("RParen", r"\)"),
    Token("LBrace", r"\{"),
    Token("RBrace", r"\}"),
    Token("Asterisk", r"\*"),
]


def read_input_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    return content


def generate_automaton():
    combined_regex = "|".join(
        "(?P<{}>{})".format(t.name.replace(" ", "_"), t.regex) for t in TOKENS
    )
    automaton = re.compile(combined_regex)
    return automaton


def analyze_input(automaton, input_str):
    tokens = []
    current_pos = 0
    line_number = 1
    column_number = 1

    rules = {}

    while current_pos < len(input_str):
        match = automaton.match(input_str, current_pos)
        if match:
            token_type = match.lastgroup
            if token_type == "Let":
                # Parse the rule definition
                rule_name_match = automaton.match(input_str, match.end())
                if rule_name_match and rule_name_match.lastgroup == "Identificador":
                    rule_name = rule_name_match.group()
                    current_pos = rule_name_match.end()
                else:
                    raise ValueError(
                        f"Error en la línea {line_number}, columna {column_number}: se esperaba un identificador de regla después de 'let'."
                    )

                equal_match = automaton.match(input_str, current_pos)
                if equal_match and equal_match.lastgroup == "Operador de asignación":
                    current_pos = equal_match.end()
                else:
                    raise ValueError(
                        f"Error en la línea {line_number}, columna {column_number}: se esperaba un '=' después del identificador de regla."
                    )

                rule_value = []
                rule_match = automaton.match(input_str, current_pos)
                while rule_match and rule_match.lastgroup not in {"Let", "Rule"}:
                    rule_value.append(rule_match.group())
                    current_pos = rule_match.end()
                    rule_match = automaton.match(input_str, current_pos)

                rules[rule_name] = "".join(rule_value)
            else:
                tokens.append((line_number, column_number, token_type))
                column_number += match.end() - match.start()
                current_pos = match.end()
        elif input_str[current_pos] == "\n":
            line_number += 1
            column_number = 1
            current_pos += 1
        elif input_str[current_pos].isspace():
            column_number += 1
            current_pos += 1
        else:
            print(
                f"Error léxico en la línea {line_number}, columna {column_number}: caracter no válido."
            )
            column_number += 1
            current_pos += 1

    return tokens, rules


def analyze_file(input_file_path):
    input_str = read_input_file(input_file_path)
    automaton = generate_automaton()
    analysis_result = analyze_input(automaton, input_str)

    has_lexical_errors = any(token[2].startswith("Error_") for token in analysis_result)

    if has_lexical_errors:
        for line, column, token in analysis_result:
            if token == "Error_Identificador_Largo":
                print(
                    f"Error léxico en la línea {line}, columna {column}: identificador demasiado largo."
                )
            elif token == "Error_Caracter_No_Permitido_Identificador":
                print(
                    f"Error léxico en la línea {line}, columna {column}: caracter no permitido en identificador."
                )
            elif token == "Error_Numero_Mal_Formado":
                print(
                    f"Error léxico en la línea {line}, columna {column}: número mal formado."
                )
            elif token == "Error_Comentario_No_Cerrado":
                print(
                    f"Error léxico en la línea {line}, columna {column}: comentario no cerrado."
                )
            elif token == "Error_String_No_Cerrado":
                print(
                    f"Error léxico en la línea {line}, columna {column}: string no cerrado."
                )
            elif token == "Error_Caracter_No_Valido":
                print(
                    f"Error léxico en la línea {line}, columna {column}: caracter no válido."
                )
    else:
        for line, column, token in analysis_result:
            print(f"{token.replace('_', ' ')} en línea {line}, columna {column}")


def main():
    # Especifica la ruta del archivo de entrada aquí
    input_file_path = "yalex1.yal"
    # input_file_path = "yalex2.yal"
    # input_file_path = "yalex3.yal"

    analyze_file(input_file_path)


if __name__ == "__main__":
    main()
