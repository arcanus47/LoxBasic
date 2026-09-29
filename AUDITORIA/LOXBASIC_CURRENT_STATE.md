# LoxBasic — Estado Actual del Proyecto

> Documento de auditoría de Fase 0
> Estado: **Completado**
> Propósito: documentar el estado real del LoxBasic original antes de realizar modificaciones o iniciar LoxBasic 2.0.

---

# 1. Propósito de esta auditoría

La Fase 0 tiene como objetivo determinar con precisión qué existe realmente en el proyecto original de LoxBasic.

La auditoría distingue entre:

1. **Documentado** — lo que aparece definido en `grammar.txt`.
2. **Implementado** — lo que realmente existe en `LoxBasic.py`.
3. **Demostrado** — lo que aparece utilizado en `cons.myopl` o `example.myopl`.
4. **Problemático / pendiente** — comportamientos que presentan posibles errores, inconsistencias o decisiones que deberán revisarse posteriormente.

La regla principal de esta fase es:

> **No modificar el código original durante la auditoría.**

LoxBasic 2.0 debe evolucionar a partir de esta base, no ignorarla.

---

# 2. Archivos auditados

Los archivos considerados relevantes para reconstruir el estado funcional original son:

```text
grammar.txt
LoxBasic.py
cons.myopl
example.myopl
strings_with_arrows.py
```

## Archivos excluidos de la reconstrucción histórica

```text
README.md
LICENSE
```

El `README.md` actual fue creado recientemente y el `LICENSE` actual tampoco corresponde al archivo histórico original.

Por lo tanto:

* no se utilizan para determinar el diseño histórico;
* no se utilizan para determinar la licencia original;
* no se utilizan para determinar la autoría histórica;
* no se utilizan para determinar las características originales del lenguaje.

---

# 3. Arquitectura real del LoxBasic original

El proyecto original es un intérprete escrito en Python.

Su flujo principal es:

```text
Código fuente LoxBasic
        ↓
      Lexer
        ↓
      Tokens
        ↓
      Parser
        ↓
       AST
        ↓
    Interpreter
        ↓
      Runtime
        ↓
      Resultado
```

La arquitectura está concentrada principalmente en:

```text
LoxBasic.py
```

y utiliza:

```text
strings_with_arrows.py
```

como componente auxiliar para representar visualmente posiciones de errores.

La implementación original contiene en un mismo archivo:

* lexer;
* tokens;
* parser;
* AST;
* resultados del parser;
* runtime;
* tipos;
* funciones;
* built-ins;
* contexto;
* tabla de símbolos;
* interpreter;
* manejo de errores;
* función `run`;
* shell interactiva.

---

# 4. Dependencias

`LoxBasic.py` importa:

```python
from strings_with_arrows import *
import string
import os
import math
```

No se identificaron dependencias externas de Python.

El proyecto utiliza principalmente:

* Python Standard Library;
* `strings_with_arrows.py`.

Por tanto, el intérprete original tiene una dependencia externa prácticamente nula.

---

# 5. Tokens implementados

El lexer reconoce los siguientes tipos:

```text
INT
FLOAT
STRING
IDENTIFIER
KEYWORD

PLUS
MINUS
MUL
DIV
POW

EQ

LPAREN
RPAREN
LSQUARE
RSQUARE

EE
NE
LT
GT
LTE
GTE

COMMA
ARROW

NEWLINE
EOF
```

Operadores implementados:

```text
+
-
*
/
^
=
==
!=
<
>
<=
>=
```

También existen:

```text
(
)
[
]
,
->
```

---

# 6. Palabras reservadas

Las palabras reservadas implementadas son:

```text
VAR
AND
OR
NOT
IF
ELIF
ELSE
FOR
TO
STEP
WHILE
FUN
THEN
END
RETURN
CONTINUE
BREAK
```

---

# 7. Comentarios

El lexer permite comentarios utilizando:

```text
#
```

Ejemplo:

```text
# Este es un comentario
PRINT("Hola")
```

Sin embargo, los comentarios no aparecen documentados explícitamente en `grammar.txt`.

Por tanto:

```text
Documentado:    ❌
Implementado:   ✅
Demostrado:     ✅
```

`example.myopl` contiene un comentario:

```text
# Esta es una pieza de software muy util
```

---

# 8. Separador de instrucciones

El lexer convierte tanto:

```text
\n
```

como:

```text
;
```

en `NEWLINE`.

Por tanto, `;` puede utilizarse como separador de instrucciones.

Ejemplo conceptual:

```text
VAR x = 10; PRINT(x)
```

Sin embargo, `;` no aparece documentado en `grammar.txt`.

Estado:

```text
Documentado:    ❌
Implementado:   ✅
Demostrado:     ❌
```

---

# 9. Tipos de datos

El runtime original contiene los siguientes tipos principales:

```text
Number
String
List
Function
BuiltInFunction
```

Además existe:

```text
Value
```

como clase base.

---

# 10. Números

`Number` representa:

* enteros;
* números decimales.

El lexer distingue:

```text
INT
FLOAT
```

Los números soportan:

```text
+
-
*
/
^
==
!=
<
>
<=
>=
AND
OR
NOT
```

La división entre cero genera un `RTError`.

---

# 11. Booleanos

No existe una clase `Boolean` independiente.

Los booleanos se representan mediante números:

```text
FALSE = 0
TRUE  = 1
```

También:

```text
Number.false = Number(0)
Number.true = Number(1)
```

La verdad lógica de un número depende de:

```text
valor != 0
```

Por tanto:

```text
0     → falso
otro  → verdadero
```

---

# 12. Strings

`String` permite:

```text
+
```

para concatenación.

También permite:

```text
String * Number
```

para repetir un string.

La condición de verdad de un string depende de si está vacío:

```text
""       → falso
"Hola"   → verdadero
```

Los strings soportan escapes como:

```text
\n
\t
```

---

# 13. Listas

El lenguaje soporta listas:

```text
[]
```

y:

```text
[1, 2, 3]
```

Las listas pueden:

* crearse;
* pasarse como argumentos;
* retornarse desde funciones;
* modificarse;
* acceder a sus elementos;
* utilizarse con `LEN`;
* utilizarse con `APPEND`;
* utilizarse con `POP`;
* utilizarse con `EXTEND`.

Una característica particular del lenguaje original es el acceso a elementos mediante `/`.

Ejemplo real:

```text
elementos/i
```

Esto significa conceptualmente:

```text
elementos[i]
```

pero la sintaxis histórica de LoxBasic utiliza `/`.

---

# 14. Sobrecarga de `/`

El operador `/` tiene más de un significado.

Para números:

```text
10 / 2
```

significa división.

Para listas:

```text
lista / indice
```

significa acceso a un elemento.

Esto debe registrarse como una decisión sintáctica histórica del lenguaje.

No debe modificarse durante esta auditoría.

Su conveniencia deberá evaluarse posteriormente en la especificación de LoxBasic 2.0.

---

# 15. Operaciones de listas

Las operaciones implementadas incluyen:

```text
lista + elemento
```

Agrega un elemento.

```text
lista - indice
```

Elimina un elemento mediante índice.

```text
lista * otra_lista
```

Extiende la lista.

```text
lista / indice
```

Obtiene un elemento.

Además existen built-ins específicos:

```text
APPEND
POP
EXTEND
LEN
```

---

# 16. Variables

La sintaxis documentada es:

```text
VAR nombre = expresion
```

Ejemplo:

```text
VAR i = 0
```

Las variables se almacenan mediante `SymbolTable`.

La tabla de símbolos soporta búsqueda en tablas padre.

Esto proporciona un sistema básico de scopes.

---

# 17. Contextos y scopes

El runtime posee:

```text
Context
SymbolTable
```

Las funciones crean contextos hijos.

Cada contexto puede tener una tabla de símbolos cuyo padre es la tabla del contexto anterior.

Esto permite:

```text
scope actual
      ↓
scope padre
      ↓
scope global
```

La resolución de variables busca primero en el contexto actual y posteriormente en sus padres.

---

# 18. Operadores aritméticos

Los operadores implementados son:

```text
+
-
*
/
^
```

Existe soporte para operadores unarios:

```text
+
-
```

Ejemplos:

```text
-10
+10
```

---

# 19. Operadores de comparación

El runtime implementa:

```text
==
!=
<
>
<=
>=
```

Existe una discrepancia importante:

`grammar.txt` no documenta explícitamente:

```text
!=
```

pero `LoxBasic.py` sí lo implementa y `example.myopl` lo utiliza.

Por tanto:

```text
!=
```

queda confirmado como una característica real del lenguaje original.

---

# 20. Operadores lógicos

Se implementan:

```text
AND
OR
NOT
```

Ejemplos conceptuales:

```text
x AND y
x OR y
NOT x
```

`AND` y `OR` forman parte de la expresión lógica.

---

# 21. Condicionales

El lenguaje soporta:

```text
IF
ELIF
ELSE
THEN
END
```

Puede utilizarse un `IF` de una sola línea:

```text
IF condicion THEN PRINT("Hola")
```

También un bloque:

```text
IF condicion THEN
    PRINT("Hola")
END
```

Esto está demostrado en `example.myopl`.

---

# 22. `ELIF` y `ELSE`

La gramática y el parser soportan:

```text
ELIF
ELSE
```

La implementación permite cadenas de condiciones.

No existe evidencia en los ejemplos auditados de uso real de `ELIF` o `ELSE`.

Por tanto:

```text
Implementado:   ✅
Ejemplo:        ❌
```

---

# 23. Bucles `FOR`

Sintaxis:

```text
FOR variable = inicio TO final THEN
    ...
END
```

También se permite:

```text
STEP
```

Ejemplo:

```text
FOR i = 1 TO 10 THEN
    PRINT(i)
END
```

---

# 24. Semántica de `FOR`

El límite superior es exclusivo.

Por ejemplo:

```text
FOR i = 0 TO 5 THEN
```

itera:

```text
0
1
2
3
4
```

y no:

```text
5
```

Esto queda confirmado tanto por la implementación como por los ejemplos.

El `STEP` puede modificar el incremento.

También se soportan pasos negativos.

---

# 25. `CONTINUE`

Existe:

```text
CONTINUE
```

y está integrado con el sistema de resultados del runtime.

`cons.myopl` lo demuestra:

```text
FOR i = 1 TO 10 THEN
    PRINT(i)
    CONTINUE
END
```

Estado:

```text
Documentado:    ✅
Implementado:   ✅
Demostrado:     ✅
```

---

# 26. `BREAK`

Existe:

```text
BREAK
```

en la gramática y en el runtime.

Está implementado mediante:

```text
loop_should_break
```

No aparece utilizado en los ejemplos auditados.

---

# 27. `WHILE`

El lenguaje implementa:

```text
WHILE condicion THEN
    ...
END
```

El parser y el interpreter contienen soporte para `WHILE`.

No aparece utilizado en los ejemplos auditados.

---

# 28. Funciones

La sintaxis principal es:

```text
FUN nombre(parametros)
    ...
END
```

También existe una forma de expresión:

```text
FUN nombre(parametros) -> expresion
```

Ejemplo real:

```text
FUN oopify(prefix) -> prefix + "oop"
```

---

# 29. Funciones con retorno

Las funciones pueden utilizar:

```text
RETURN expresion
```

Ejemplo:

```text
RETURN resultado
```

Si una función de bloque no ejecuta un `RETURN`, el runtime puede retornar `Number.null`.

---

# 30. Funciones de una expresión

La forma:

```text
FUN nombre(x) -> expresion
```

funciona como una función con retorno automático.

Ejemplo:

```text
FUN oopify(prefix) -> prefix + "oop"
```

Es una característica real y demostrada.

---

# 31. Funciones anónimas

El parser permite que el nombre de una función sea opcional.

Esto permite funciones anónimas.

El runtime utiliza:

```text
<anonymous>
```

como nombre interno cuando corresponde.

No existe un ejemplo auditado de función anónima explícita, pero la capacidad está implementada.

---

# 32. Funciones como valores

Una característica importante del runtime es que las funciones pueden ser utilizadas como valores.

`example.myopl` demuestra:

```text
FUN map(elementos, func)
```

y posteriormente:

```text
map(["l", "sp"], oopify)
```

Dentro de `map()`:

```text
func(elementos/i)
```

Por tanto, las funciones pueden:

* pasarse como argumentos;
* almacenarse en variables;
* invocarse posteriormente.

Esto proporciona una forma básica de funciones de primera clase.

---

# 33. Composición de funciones

`example.myopl` contiene:

```text
PRINT(join(map(["l", "sp"], oopify), ", "))
```

La expresión demuestra composición:

```text
["l", "sp"]
      ↓
    map
      ↓
["loop", "spoop"]
      ↓
    join
      ↓
"loop, spoop"
      ↓
   PRINT
```

Esto confirma que el lenguaje permite expresiones anidadas y composición de llamadas.

---

# 34. Built-ins

El runtime original proporciona:

```text
PRINT
PRINT_RET
INPUT
INPUT_INT
CLEAR
CLS
IS_NUM
IS_STR
IS_LIST
IS_FUN
APPEND
POP
EXTEND
LEN
RUN
```

Estas funciones forman una pequeña biblioteca estándar integrada.

---

# 35. Entrada y salida

Salida:

```text
PRINT(valor)
PRINT_RET(valor)
```

Entrada:

```text
INPUT()
INPUT_INT()
```

`INPUT_INT()` repite la solicitud hasta obtener un entero válido.

Esto proporciona interacción básica con consola.

---

# 36. Ejecución de archivos

Existe:

```text
RUN
```

El built-in `RUN` recibe un archivo, lo lee y ejecuta mediante:

```text
run(fn, script)
```

Por tanto, el lenguaje original no estaba limitado exclusivamente a ejecutar una instrucción aislada en consola.

Tiene soporte para ejecutar scripts externos.

---

# 37. Tabla de símbolos global

El entorno global contiene:

```text
NULL
FALSE
TRUE
MATH_PI

PRINT
PRINT_RET
INPUT
INPUT_INT
CLEAR
CLS

IS_NUM
IS_STR
IS_LIST
IS_FUN

APPEND
POP
EXTEND
LEN
RUN
```

Esto representa el entorno inicial disponible para los programas.

---

# 38. Manejo de errores

Existen diferentes clases:

```text
Error
IllegalCharError
ExpectedCharError
InvalidSyntaxError
RTError
```

Los errores contienen posiciones:

```text
pos_start
pos_end
```

y los errores de runtime tienen contexto.

---

# 39. Tracebacks

`Context` contiene información para construir una cadena de traceback.

Los errores de runtime pueden mostrar la cadena de contextos:

```text
programa
  ↓
función A
  ↓
función B
  ↓
error
```

Esto es una base importante para el diagnóstico de errores.

---

# 40. Errores visuales

`strings_with_arrows.py` genera indicadores visuales utilizando:

```text
^
```

Ejemplo conceptual:

```text
PRINT(x +
      ^^^
```

El sistema:

* localiza línea;
* calcula columna;
* determina rango;
* muestra el código;
* muestra flechas `^`.

Puede trabajar con rangos de varias líneas.

---

# 41. Limitaciones del sistema de errores

El sistema original no contiene:

* sugerencias automáticas;
* correcciones propuestas;
* explicación educativa;
* mensajes estructurados;
* resaltado avanzado;
* diagnóstico contextual moderno;
* sistema de severidades.

Por tanto existe una infraestructura básica de localización, pero no un sistema educativo de diagnóstico.

---

# 42. Shell interactiva

Al final de `LoxBasic.py` existe una consola:

```text
LoxBasic >
```

El usuario puede introducir código y ejecutar:

```text
LoxBasic.run('<stdin>', text)
```

El resultado se imprime en la consola.

---

# 43. Problema arquitectónico del shell

El propio `LoxBasic.py` contiene:

```python
import LoxBasic
```

y posteriormente inicia el shell.

Esto mezcla:

```text
motor del lenguaje
```

con:

```text
interfaz de consola
```

y genera una arquitectura poco limpia para una futura distribución.

No se modifica durante Fase 0.

Debe registrarse como una de las cuestiones arquitectónicas a resolver posteriormente.

---

# 44. Indentación

Los ejemplos utilizan indentación:

```text
FOR ...
    PRINT(...)
END
```

pero la indentación no forma parte de la gramática.

No existen tokens equivalentes a:

```text
INDENT
DEDENT
```

Los bloques se delimitan mediante:

```text
THEN
...
END
```

Por tanto la indentación es principalmente visual.

---

# 45. `cons.myopl`

El archivo contiene:

```text
VAR i = 0

FOR i = 1 TO 10 THEN
    PRINT(i)
    CONTINUE
END
```

Demuestra:

* variables;
* `FOR`;
* `THEN`;
* bloque multilínea;
* `PRINT`;
* `CONTINUE`;
* `END`.

Además confirma el comportamiento del `FOR` con límite superior exclusivo.

---

# 46. `example.myopl`

Este archivo constituye una demostración mucho más completa.

Incluye:

```text
FUN oopify(prefix) -> prefix + "oop"
```

```text
FUN join(elementos, separador)
```

```text
FUN map(elementos, func)
```

listas:

```text
["l", "sp"]
```

funciones como argumentos:

```text
map(["l", "sp"], oopify)
```

acceso a listas:

```text
elementos/i
```

condicional:

```text
IF i != len - 1 THEN ...
```

y composición:

```text
PRINT(join(map(["l", "sp"], oopify), ", "))
```

Este archivo demuestra que el lenguaje original tenía una expresividad superior a un BASIC puramente introductorio.

---

# 47. Matriz de capacidades

| Característica          | Documentada | Implementada | Demostrada |
| ----------------------- | :---------: | :----------: | :--------: |
| Variables               |      ✅      |       ✅      |      ✅     |
| Enteros                 |      ✅      |       ✅      |      ✅     |
| Decimales               |      ✅      |       ✅      |      —     |
| Strings                 |      ✅      |       ✅      |      ✅     |
| Listas                  |      ✅      |       ✅      |      ✅     |
| `+`                     |      ✅      |       ✅      |      ✅     |
| `-`                     |      ✅      |       ✅      |      —     |
| `*`                     |      ✅      |       ✅      |      —     |
| `/`                     |      ✅      |       ✅      |      ✅     |
| `^`                     |      ✅      |       ✅      |      —     |
| `==`                    |      ✅      |       ✅      |      —     |
| `!=`                    |      ❌      |       ✅      |      ✅     |
| `<`                     |      ✅      |       ✅      |      —     |
| `>`                     |      ✅      |       ✅      |      —     |
| `<=`                    |      ✅      |       ✅      |      —     |
| `>=`                    |      ✅      |       ✅      |      —     |
| `AND`                   |      ✅      |       ✅      |      —     |
| `OR`                    |      ✅      |       ✅      |      —     |
| `NOT`                   |      ✅      |       ✅      |      —     |
| `IF`                    |      ✅      |       ✅      |      ✅     |
| `ELIF`                  |      ✅      |       ✅      |      —     |
| `ELSE`                  |      ✅      |       ✅      |      —     |
| `FOR`                   |      ✅      |       ✅      |      ✅     |
| `STEP`                  |      ✅      |       ✅      |      —     |
| `WHILE`                 |      ✅      |       ✅      |      —     |
| `BREAK`                 |      ✅      |       ✅      |      —     |
| `CONTINUE`              |      ✅      |       ✅      |      ✅     |
| `FUN`                   |      ✅      |       ✅      |      ✅     |
| Funciones con expresión |      ✅      |       ✅      |      ✅     |
| Funciones multilínea    |      ✅      |       ✅      |      ✅     |
| Parámetros              |      ✅      |       ✅      |      ✅     |
| `RETURN`                |      ✅      |       ✅      |      ✅     |
| Funciones anónimas      |      ✅      |       ✅      |      —     |
| Funciones como valores  |  implícito  |       ✅      |      ✅     |
| `PRINT`                 |      —      |       ✅      |      ✅     |
| `INPUT`                 |      —      |       ✅      |      —     |
| `LEN`                   |      —      |       ✅      |      ✅     |
| `APPEND`                |      —      |       ✅      |      ✅     |
| `POP`                   |      —      |       ✅      |      —     |
| `EXTEND`                |      —      |       ✅      |      —     |
| `RUN`                   |      —      |       ✅      |      —     |
| Comentarios `#`         |      ❌      |       ✅      |      ✅     |
| `;` como separador      |      ❌      |       ✅      |      —     |
| Scopes                  |      —      |       ✅      |  indirecto |
| Tracebacks              |      —      |       ✅      |      —     |
| Errores con posición    |      —      |       ✅      |      —     |

---

# 48. Discrepancias confirmadas

## 48.1 `!=`

`grammar.txt` no incluye:

```text
!=
```

pero:

* el lexer lo reconoce;
* el parser lo acepta;
* `Number` lo implementa;
* `example.myopl` lo utiliza.

Conclusión:

> `!=` pertenece al lenguaje implementado, pero falta documentarlo en la gramática.

---

## 48.2 Comentarios

El lexer soporta:

```text
#
```

pero `grammar.txt` no los describe.

Conclusión:

> Los comentarios existen en la implementación y son utilizados en `example.myopl`.

---

## 48.3 `;`

El lexer permite utilizar `;` como `NEWLINE`.

No aparece documentado en `grammar.txt`.

Conclusión:

> Es una característica implementada pero no documentada.

---

# 49. Posibles problemas técnicos identificados

Estos puntos fueron detectados durante la revisión del código.

No han sido modificados.

---

## 49.1 Comentario hasta EOF

El procesamiento de comentarios utiliza un bucle hasta encontrar `\n`.

Si un comentario termina exactamente al final del archivo sin salto de línea, debe probarse si el lexer maneja correctamente ese caso.

Estado:

```text
Pendiente de prueba.
```

---

## 49.2 `CLEAR` / `CLS`

La implementación utiliza:

```python
os.system('cls' if os.name == 'nt' else 'cls')
```

Por tanto utiliza `cls` tanto en Windows como en sistemas no Windows.

Esto puede provocar que:

```text
CLEAR
CLS
```

no funcionen correctamente en Linux/macOS.

Estado:

```text
Posible problema de portabilidad.
```

---

## 49.3 Índices de listas

Las operaciones de listas utilizan valores provenientes de `Number`.

Debe comprobarse qué ocurre cuando se utiliza un índice decimal.

Por ejemplo:

```text
lista / 1.5
```

La implementación puede terminar interactuando con mecanismos de Python que esperan un índice entero.

Estado:

```text
Pendiente de prueba.
```

---

## 49.4 Copia de listas

La implementación realiza una copia superficial:

```text
List(self.elements)
```

Esto significa que elementos internos pueden compartir referencias.

Esto puede ser correcto dependiendo del diseño, pero debe documentarse o evaluarse posteriormente.

Estado:

```text
Decisión semántica pendiente.
```

---

## 49.5 Verdad lógica de listas

`List` no sobrescribe `is_true()`.

Por tanto hereda el comportamiento de `Value`.

Esto significa que debe comprobarse el comportamiento de:

```text
IF [] THEN ...
```

y:

```text
IF [1] THEN ...
```

Estado:

```text
Semántica pendiente de prueba.
```

---

## 49.6 Arquitectura monolítica

Gran parte del lenguaje se encuentra en:

```text
LoxBasic.py
```

Esto dificulta:

* mantenimiento;
* pruebas unitarias;
* evolución;
* separación de responsabilidades;
* reutilización del runtime;
* creación de herramientas externas.

No es necesariamente un defecto del lenguaje, pero sí una limitación arquitectónica para una futura versión moderna.

---

## 49.7 Shell mezclada con el motor

El mismo archivo contiene:

```text
motor del lenguaje
+
shell interactiva
```

Esto debería separarse en una futura reorganización.

No se modifica en Fase 0.

---

# 50. Características que NO deben darse por existentes

Durante la auditoría no se encontró evidencia en los archivos revisados de:

```text
Módulos
Clases
Objetos
Diccionarios
Excepciones del lenguaje
Import
Paquetes
Archivos como tipo nativo
Async/Await
Generadores
Pattern matching
Sistema de tipos estático
Tipado de variables
Interfaces
Debugger
IDE
LSP
Autocompletado
Educational Mode implementado en LoxBasic.py
```

Esto no significa necesariamente que nunca hayan existido en algún momento histórico.

Significa:

> **No forman parte del núcleo actualmente auditado.**

---

# 51. Educational Mode

La visión histórica del proyecto menciona un modo especial de ejecución/educación.

Sin embargo, dentro de los archivos funcionales auditados:

```text
LoxBasic.py
grammar.txt
cons.myopl
example.myopl
strings_with_arrows.py
```

no se identificó una implementación clara de un modo educativo independiente.

Por tanto debe clasificarse como:

```text
Estado: no confirmado en el núcleo auditado.
```

No debe afirmarse todavía que nunca existió.

---

# 52. Naturaleza real del proyecto original

Después de la auditoría, LoxBasic puede describirse técnicamente como:

> Un lenguaje interpretado de propósito educativo, con sintaxis inspirada en BASIC/pseudocódigo, implementado en Python, con lexer, parser, AST, runtime e intérprete propios.

Su núcleo soporta:

```text
Variables
Números
Strings
Listas
Operadores
Condicionales
Bucles
Funciones
Retornos
Funciones como valores
Scopes
Entrada/salida
Built-ins
Ejecución de archivos
Errores con posiciones
Tracebacks
```

No es solamente un parser ni un pseudocódigo.

Es un **lenguaje ejecutable real**.

---

# 53. Nivel de expresividad encontrado

Aunque su sintaxis es sencilla, el runtime tiene características relativamente avanzadas para una primera versión:

```text
Funciones de primera clase
Funciones anónimas
Scopes
Funciones como argumentos
Listas mutables
Composición de funciones
Funciones de expresión
```

El ejemplo `example.myopl` demuestra que el lenguaje podía expresar abstracciones como:

```text
map()
join()
```

sin soporte especial del intérprete para esas funciones.

Esto es significativo para el diseño futuro.

---

# 54. Principios de preservación para LoxBasic 2.0

La auditoría no determina todavía qué características deben conservarse definitivamente.

Sin embargo, antes de eliminar cualquier característica del lenguaje original deberá evaluarse:

```text
¿Está implementada?
¿Está demostrada?
¿Tiene valor educativo?
¿Tiene problemas técnicos?
¿Es coherente con la futura especificación?
¿Existen programas originales que dependan de ella?
```

La evolución debe ser incremental.

---

# 55. Elementos que requieren revisión en fases posteriores

Los siguientes elementos quedan registrados para análisis futuro:

```text
Acceso a listas mediante /
Semántica de TO
Semántica de STEP
Funciones como valores
Funciones anónimas
Scopes
Mutabilidad de listas
Representación booleana mediante Number
Sistema de errores
Tracebacks
Built-ins
RUN
CLEAR / CLS
Arquitectura monolítica
Shell integrada
Sintaxis de bloques
Sintaxis de funciones
Comentarios
Separador ;
```

No deben modificarse durante esta auditoría.

---

# 56. Separación para LoxBasic 2.0

La evolución futura debe partir de cuatro categorías:

## Preservar

Características que funcionan y forman parte importante de la identidad del lenguaje.

Ejemplos potenciales:

```text
Variables
IF
FOR
WHILE
FUN
RETURN
Listas
PRINT
Entrada básica
Errores con ubicación
```

---

## Revisar

Características existentes cuyo diseño merece evaluación.

Ejemplos:

```text
Acceso mediante /
Booleanos como Number
Semántica de listas
Scopes
Funciones como valores
Built-ins
TO exclusivo
```

---

## Corregir

Problemas técnicos confirmados mediante pruebas.

Ejemplos potenciales:

```text
Portabilidad de CLEAR/CLS
Errores de índices
Problemas de lexer
Problemas de diagnóstico
```

---

## Rediseñar

Partes de infraestructura que limitan el crecimiento del proyecto.

Ejemplos:

```text
LoxBasic.py monolítico
Shell mezclada con runtime
Sistema de pruebas
Organización del proyecto
Sistema de diagnóstico
Documentación formal
```

---

# 57. Estado de Fase 0

## Auditoría completada

Se revisaron:

```text
✅ grammar.txt
✅ LoxBasic.py
✅ cons.myopl
✅ example.myopl
✅ strings_with_arrows.py
```

Se excluyeron correctamente:

```text
🚫 README.md actual
🚫 LICENSE actual
```

porque no representan documentación/artefactos históricos originales.

---

# 58. Resultado final de Fase 0

La auditoría confirma que LoxBasic posee una base real de lenguaje interpretado:

```text
                 LOXBASIC ORIGINAL
                        │
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
      Lexer           Parser           Runtime
        │               │                │
      Tokens            AST         SymbolTable
                                        │
                                   Interpreter
                                        │
                                  Built-ins
                                        │
                                  Error System
```

La base funcional original es suficientemente amplia como para iniciar una evolución hacia una versión moderna sin necesidad de crear el lenguaje desde cero.

La siguiente fase debe centrarse en **estabilizar y comprender completamente esta implementación antes de añadir características importantes**.

---

# 59. Regla para las siguientes fases

> **No agregar complejidad antes de estabilizar la base.**

La evolución propuesta será:

```text
FASE 0
Auditoría
    ↓
FASE 1
Estabilización
    ↓
FASE 2
Especificación formal LoxBasic 2.0
    ↓
FASE 3
Entorno de desarrollo
    ↓
FASE 4
Nivel educativo inicial
    ↓
FASE 5
Documentación y ejemplos
    ↓
FASE 6
Beta pública
    ↓
FASE 7
LoxBasic 2.0 estable
```

---

# 60. Principio central del proyecto

LoxBasic no debe convertirse simplemente en un lenguaje con más características.

La dirección del proyecto debe mantenerse alrededor de:

> **Simplificar la programación, no ocultarla.**

Y la transición educativa prevista:

```text
Pseudocódigo
      ↓
  LoxBasic
      ↓
Programación real
      ↓
Lenguajes profesionales
```

El objetivo de LoxBasic 2.0 será proporcionar una entrada progresiva a la programación real sin eliminar los conceptos fundamentales que posteriormente necesitará el estudiante.

---

# Estado

**Fase 0 — AUDITORÍA DEL PROYECTO ORIGINAL: COMPLETADA**

**Código original modificado durante esta fase: NO**

**Base preparada para Fase 1 — Estabilización.**
