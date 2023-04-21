let if = "if"
let for = "for"
let digito = "0|1|2|3|4|5|6|7|8|9"
let numero = "digito(digito)*"
let numerodecimal = "(((digito)+\\.(digito)*)|(\\.(digito)+))"
let letra = "a|b|c|d|e|f|g|A|B|C|D|E|F|G"
let identificador = "letra(letra|digito)*xyz"
let espacio = "\\s"
let contenidocadena = "((numero|letra|espacio)+)"
let cadena = "\"contenidocadena\""

rule tokens =
  if { print("if\n") }
  | for { print("for\n") }
  | digito			{ print("Dígito\n") }
  | numero			{ print("Numero\n") }
  | numerodecimal { print("Numero Decimal\n") }
  | letra			{ print("Letra\n") }
  | identificador	{ print("Identificador\n") }
  | cadena         { print("Cadena\n") }
