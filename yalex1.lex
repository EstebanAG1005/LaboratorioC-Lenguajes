let if = "if"
let digito = "0|1|2|3|4|5|6|7|8|9"
let hexadec = "0|1|2|3|4|5|6|7|8|9|a|b|c|d|e|f|A|B|C|D|E|F"
let numero = "digito(digito)*"
let numerodecimal = "((digito)*\\.(digito)+|(digito)+\\.(digito)*)"
let numerohexadecimal = "0xX(hexadec)+"
let letra = "A|B|C|D|E|F|G"
let identificador = "letra(letra|digito)*"

rule tokens =
  if { print("if\n") }
  | digito			{ print("Dígito\n") }
  | hexadec  { print("hexadec\n") }
  | numero			{ print("Numero\n") }
  | numerodecimal { print("Numero Decimal\n") }
  | numerohexadecimal { print("Numero Hexadecimal\n") } 
  | letra			{ print("Letra\n") }
  | identificador	{ print("Identificador\n") }
  



