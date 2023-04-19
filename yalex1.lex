let if = "if"
let digito = "2|1"
let numero = "digito(digito)*"
let letra = "a|b"
let identificador = "letra(letra|digito)*"

rule tokens =
  if	{ print("IF\n") }
  | identificador	{ print("Identificador\n") }
  | digito			{ print("Dígito\n") }
  | letra			{ print("Letra\n") }
  | numero			{ print("Número\n") }

