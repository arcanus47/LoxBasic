import unittest
from pathlib import Path


# ============================================================
# CARGA CONTROLADA DEL MOTOR ORIGINAL
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = PROJECT_ROOT / "LoxBasic.py"

source = SOURCE_PATH.read_text(encoding="utf-8")

shell_marker = (
    "###################################\n"
    "# SHELL\n"
    "###################################"
)

if shell_marker not in source:
    raise RuntimeError(
        "No se encontró el marcador del SHELL en LoxBasic.py"
    )

engine_source = source.split(shell_marker, 1)[0]

namespace = {
    "__name__": "__loxbasic_baseline__",
    "__file__": str(SOURCE_PATH),
}

exec(
    compile(engine_source, str(SOURCE_PATH), "exec"),
    namespace
)

run = namespace["run"]


# ============================================================
# HELPERS
# ============================================================

def execute(code):
    """
    Ejecuta código LoxBasic y devuelve:

        value, error
    """
    return run("<baseline>", code)


def execute_ok(code):
    """
    Ejecuta código y falla el test si LoxBasic devuelve error.
    """
    value, error = execute(code)

    if error is not None:
        raise AssertionError(
            "LoxBasic produjo un error para:\n{}\n\n{}".format(
                code,
                error.as_string()
            )
        )

    if value is None:
        raise AssertionError(
            "LoxBasic no produjo ningún resultado para:\n{}".format(code)
        )

    return value


def results(value):
    """
    Convierte el List que devuelve el programa en sus elementos.
    """
    if not hasattr(value, "elements"):
        raise AssertionError(
            "Se esperaba un resultado List, se obtuvo: {}".format(
                type(value).__name__
            )
        )

    return value.elements


def first_result(code):
    """
    Ejecuta código y devuelve el primer resultado.
    """
    value = execute_ok(code)
    items = results(value)

    if len(items) == 0:
        raise AssertionError(
            "El programa no produjo ningún elemento:\n{}".format(code)
        )

    return items[0]


def number_result(code):
    """
    Ejecuta código y devuelve el valor numérico del primer resultado.
    """
    value = first_result(code)

    if not hasattr(value, "value"):
        raise AssertionError(
            "Se esperaba un Number, se obtuvo: {}".format(
                type(value).__name__
            )
        )

    return value.value


def string_result(code):
    """
    Ejecuta código y devuelve el valor textual del primer resultado.
    """
    value = first_result(code)

    if not hasattr(value, "value"):
        raise AssertionError(
            "Se esperaba un String, se obtuvo: {}".format(
                type(value).__name__
            )
        )

    return value.value


def expect_error(code, error_type=None):
    """
    Comprueba que el código produzca un error de LoxBasic.
    """
    value, error = execute(code)

    if error is None:
        raise AssertionError(
            "Se esperaba un error para:\n{}".format(code)
        )

    if error_type is not None:
        if not isinstance(error, error_type):
            raise AssertionError(
                "Se esperaba {}, se obtuvo {}.\n\n{}".format(
                    error_type.__name__,
                    type(error).__name__,
                    error.as_string()
                )
            )

    return error


# ============================================================
# BASELINE COMPLETO
# ============================================================

class LoxBasicBaselineTests(unittest.TestCase):

    # --------------------------------------------------------
    # 001 - ARITMÉTICA
    # --------------------------------------------------------

    def test_001_basic_addition(self):
        self.assertEqual(
            number_result("1 + 2"),
            3
        )

    def test_002_subtraction(self):
        self.assertEqual(
            number_result("10 - 3"),
            7
        )

    def test_003_multiplication(self):
        self.assertEqual(
            number_result("4 * 5"),
            20
        )

    def test_004_division(self):
        self.assertEqual(
            number_result("20 / 4"),
            5
        )

    def test_005_power(self):
        self.assertEqual(
            number_result("2 ^ 3"),
            8
        )

    def test_006_operator_precedence(self):
        self.assertEqual(
            number_result("2 + 3 * 4"),
            14
        )

    def test_007_parentheses(self):
        self.assertEqual(
            number_result("(2 + 3) * 4"),
            20
        )

    def test_008_unary_minus(self):
        self.assertEqual(
            number_result("-5"),
            -5
        )

    def test_009_unary_plus(self):
        self.assertEqual(
            number_result("+5"),
            5
        )

    # --------------------------------------------------------
    # 002 - VARIABLES
    # --------------------------------------------------------

    def test_010_variable_declaration(self):
        value, error = execute("VAR x = 10")

        self.assertIsNone(error)
        self.assertIsNotNone(value)

    def test_011_variable_usage(self):
        self.assertEqual(
            number_result(
                """
VAR x = 10
x + 5
"""
            ),
            15
        )

    def test_012_variable_reassignment(self):
        self.assertEqual(
            number_result(
                """
VAR x = 10
VAR x = 20
x
"""
            ),
            20
        )

    def test_013_variable_expression(self):
        self.assertEqual(
            number_result(
                """
VAR x = 5
VAR y = 10
x + y
"""
            ),
            15
        )

    # --------------------------------------------------------
    # 003 - STRINGS
    # --------------------------------------------------------

    def test_014_string_literal(self):
        self.assertEqual(
            string_result('"Hola"'),
            "Hola"
        )

    def test_015_string_concatenation(self):
        self.assertEqual(
            string_result('"Hola " + "Mundo"'),
            "Hola Mundo"
        )

    def test_016_string_multiplication(self):
        self.assertEqual(
            string_result('"Hi" * 3'),
            "HiHiHi"
        )

    def test_017_string_escape_newline(self):
        self.assertEqual(
            string_result('"Hola\\nMundo"'),
            "Hola\nMundo"
        )

    def test_018_string_escape_tab(self):
        self.assertEqual(
            string_result('"Hola\\tMundo"'),
            "Hola\tMundo"
        )

    # --------------------------------------------------------
    # 004 - LISTAS
    # --------------------------------------------------------

    def test_019_empty_list(self):
        value = execute_ok("[]")
        items = results(value)

        self.assertEqual(len(items), 1)
        self.assertEqual(type(items[0]).__name__, "List")

    def test_020_list_literal(self):
        value = execute_ok("[1, 2, 3]")
        items = results(value)

        self.assertEqual(len(items), 1)

        lst = items[0]

        self.assertEqual(
            [item.value for item in lst.elements],
            [1, 2, 3]
        )

    def test_021_list_access(self):
        self.assertEqual(
            number_result("[10, 20, 30] / 1"),
            20
        )

    def test_022_list_append(self):
        self.assertEqual(
            number_result(
                """
VAR lista = [1, 2]
APPEND(lista, 3)
LEN(lista)
"""
            ),
            3
        )

    def test_023_list_pop(self):
        self.assertEqual(
            number_result(
                """
VAR lista = [10, 20, 30]
POP(lista, 1)
LEN(lista)
"""
            ),
            2
        )

    def test_024_list_extend(self):
        self.assertEqual(
            number_result(
                """
VAR lista = [1]
EXTEND(lista, [2, 3])
LEN(lista)
"""
            ),
            3
        )

    def test_025_list_len(self):
        self.assertEqual(
            number_result("LEN([1, 2, 3])"),
            3
        )

    # --------------------------------------------------------
    # 005 - COMPARACIONES
    # --------------------------------------------------------

    def test_026_equal(self):
        self.assertEqual(
            number_result("5 == 5"),
            1
        )

    def test_027_not_equal(self):
        self.assertEqual(
            number_result("5 != 3"),
            1
        )

    def test_028_less_than(self):
        self.assertEqual(
            number_result("3 < 5"),
            1
        )

    def test_029_greater_than(self):
        self.assertEqual(
            number_result("5 > 3"),
            1
        )

    def test_030_less_or_equal(self):
        self.assertEqual(
            number_result("5 <= 5"),
            1
        )

    def test_031_greater_or_equal(self):
        self.assertEqual(
            number_result("5 >= 5"),
            1
        )

    # --------------------------------------------------------
    # 006 - LÓGICA
    # --------------------------------------------------------

    def test_032_and(self):
        self.assertEqual(
            number_result("1 AND 1"),
            1
        )

    def test_033_and_false(self):
        self.assertEqual(
            number_result("1 AND 0"),
            0
        )

    def test_034_or(self):
        self.assertEqual(
            number_result("0 OR 1"),
            1
        )

    def test_035_or_false(self):
        self.assertEqual(
            number_result("0 OR 0"),
            0
        )

    def test_036_not(self):
        self.assertEqual(
            number_result("NOT 0"),
            1
        )

    def test_037_not_true(self):
        self.assertEqual(
            number_result("NOT 1"),
            0
        )

    # --------------------------------------------------------
    # 007 - IF
    # --------------------------------------------------------

    def test_038_if_single_line(self):
        self.assertEqual(
            number_result("IF 1 THEN 10"),
            10
        )

    def test_039_if_false(self):
        value = execute_ok(
            "IF 0 THEN 10"
        )

        self.assertEqual(
            len(results(value)),
            1
        )

    def test_040_if_else(self):
        self.assertEqual(
            number_result(
                "IF 0 THEN 10 ELSE 20"
            ),
            20
        )

    def test_041_if_elif(self):
        self.assertEqual(
            number_result(
                "IF 0 THEN 10 ELIF 1 THEN 20 ELSE 30"
            ),
            20
        )

    # --------------------------------------------------------
    # 008 - FOR
    # --------------------------------------------------------

    def test_042_for_exclusive_end(self):
        value = execute_ok(
            """
VAR resultado = 0

FOR i = 0 TO 5 THEN
VAR resultado = resultado + 1
END

resultado
"""
        )

        self.assertEqual(
            results(value)[0].value,
            5
        )

    def test_043_for_step_positive(self):
        value = execute_ok(
            """
VAR resultado = 0

FOR i = 0 TO 10 STEP 2 THEN
VAR resultado = resultado + 1
END

resultado
"""
        )

        self.assertEqual(
            results(value)[0].value,
            5
        )

    def test_044_for_step_negative(self):
        value = execute_ok(
            """
VAR resultado = 0

FOR i = 10 TO 0 STEP -2 THEN
VAR resultado = resultado + 1
END

resultado
"""
        )

        self.assertEqual(
            results(value)[0].value,
            5
        )

    # --------------------------------------------------------
    # 009 - WHILE
    # --------------------------------------------------------

    def test_045_while_loop(self):
        self.assertEqual(
            number_result(
                """
VAR x = 0

WHILE x < 5 THEN
VAR x = x + 1
END

x
"""
            ),
            5
        )

    # --------------------------------------------------------
    # 010 - BREAK / CONTINUE
    # --------------------------------------------------------

    def test_046_continue(self):
        value, error = execute(
            """
FOR i = 0 TO 5 THEN
CONTINUE
END
"""
        )

        self.assertIsNone(error)
        self.assertIsNotNone(value)

    def test_047_break(self):
        value, error = execute(
            """
FOR i = 0 TO 5 THEN
BREAK
END
"""
        )

        self.assertIsNone(error)
        self.assertIsNotNone(value)

    # --------------------------------------------------------
    # 011 - FUNCIONES
    # --------------------------------------------------------

    def test_048_function_expression_body(self):
        self.assertEqual(
            number_result(
                """
FUN suma(a, b) -> a + b
suma(2, 3)
"""
            ),
            5
        )

    def test_049_function_multiline(self):
        self.assertEqual(
            number_result(
                """
FUN suma(a, b)
VAR resultado = a + b
RETURN resultado
END

suma(4, 6)
"""
            ),
            10
        )

    def test_050_function_return(self):
        self.assertEqual(
            number_result(
                """
FUN doble(x)
RETURN x * 2
END

doble(5)
"""
            ),
            10
        )

    def test_051_function_as_value(self):
        self.assertEqual(
            number_result(
                """
FUN doble(x) -> x * 2
VAR f = doble
f(5)
"""
            ),
            10
        )

    def test_052_anonymous_function(self):
        self.assertEqual(
            number_result(
                """
VAR f = FUN(x) -> x + 1
f(5)
"""
            ),
            6
        )

    def test_053_function_as_argument(self):
        self.assertEqual(
            number_result(
                """
FUN aplicar(func, valor)
RETURN func(valor)
END

FUN doble(x) -> x * 2

aplicar(doble, 5)
"""
            ),
            10
        )

    # --------------------------------------------------------
    # 012 - BUILT-INS / TYPE CHECKS
    # --------------------------------------------------------

    def test_054_is_num(self):
        self.assertEqual(
            number_result("IS_NUM(10)"),
            1
        )

    def test_055_is_str(self):
        self.assertEqual(
            number_result('IS_STR("Hola")'),
            1
        )

    def test_056_is_list(self):
        self.assertEqual(
            number_result("IS_LIST([1, 2])"),
            1
        )

    def test_057_is_fun(self):
        self.assertEqual(
            number_result(
                """
FUN hola() -> 1
IS_FUN(hola)
"""
            ),
            1
        )

    # --------------------------------------------------------
    # 013 - PRINT / PRINT_RET
    # --------------------------------------------------------

    def test_058_print(self):
        value, error = execute(
            'PRINT("Hola")'
        )

        self.assertIsNone(error)
        self.assertIsNotNone(value)

    def test_059_print_ret(self):
        self.assertEqual(
            string_result(
                'PRINT_RET("Hola")'
            ),
            "Hola"
        )

    # --------------------------------------------------------
    # 014 - RETURN
    # --------------------------------------------------------

    def test_060_return_from_function(self):
        self.assertEqual(
            number_result(
                """
FUN test()
RETURN 42
END

test()
"""
            ),
            42
        )

    # --------------------------------------------------------
    # 015 - COMENTARIOS
    # --------------------------------------------------------

    def test_061_comment(self):
        self.assertEqual(
            number_result(
                """
# comentario

1 + 2
"""
            ),
            3
        )

    def test_062_comment_after_code(self):
        self.assertEqual(
            number_result(
                "1 + 2 # comentario"
            ),
            3
        )

    # --------------------------------------------------------
    # 016 - NEWLINE / SEMICOLON
    # --------------------------------------------------------

    def test_063_semicolon_separator(self):
        self.assertEqual(
            number_result(
                "VAR x = 10; x + 5"
            ),
            15
        )

    # --------------------------------------------------------
    # 017 - ERRORES
    # --------------------------------------------------------

    def test_064_division_by_zero(self):
        error = expect_error("1 / 0")

        self.assertIn(
            "división por cero",
            error.as_string().lower()
        )

    def test_065_undefined_variable(self):
        error = expect_error(
            "variable_que_no_existe"
        )

        self.assertIn(
            "no está definido",
            error.as_string().lower()
        )

    def test_066_invalid_syntax(self):
        error = expect_error(
            "1 +"
        )

        self.assertIsNotNone(error)

    def test_067_invalid_list_index(self):
        error = expect_error(
            "[1, 2, 3] / 99"
        )

        self.assertIsNotNone(error)

    # --------------------------------------------------------
    # 018 - TRACEBACK
    # --------------------------------------------------------

    def test_068_function_traceback(self):
        error = expect_error(
            """
FUN dividir()
RETURN 1 / 0
END

dividir()
"""
        )

        text = error.as_string()

        self.assertIn(
            "división por cero",
            text.lower()
        )

        self.assertIn(
            "Rastreo",
            text
        )

    # --------------------------------------------------------
    # 019 - EJEMPLO REAL DEL PROYECTO
    # --------------------------------------------------------

    def test_069_example_oopify(self):
        self.assertEqual(
            string_result(
                """
FUN oopify(prefix) -> prefix + "oop"
oopify("l")
"""
            ),
            "loop"
        )

    def test_070_map_style_program(self):
        value = execute_ok(
            """
FUN doble(x) -> x * 2

VAR valores = [1, 2, 3]
VAR resultado = []

FOR i = 0 TO LEN(valores) THEN
APPEND(resultado, doble(valores / i))
END

resultado
"""
        )

        lst = results(value)[0]

        self.assertEqual(
            [item.value for item in lst.elements],
            [2, 4, 6]
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
