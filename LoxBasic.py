#######################################
# LOXBASIC
# Intérprete completo
#######################################

from strings_with_arrows import *

import string
import os
import math
import time


#######################################
# CONSTANTES
#######################################

DIGITS = "0123456789"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS + "_"


#######################################
# ERRORES
#######################################


class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}\n"
        result += f"Archivo {self.pos_start.fn}, línea {self.pos_start.ln + 1}"
        result += "\n\n" + string_with_arrows(
            self.pos_start.ftxt, self.pos_start, self.pos_end
        )
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Caracter ilegal", details)


class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Carácter esperado", details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "Sintaxis inválida", details)


class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Error de tiempo de ejecución", details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        result += "\n\n" + string_with_arrows(
            self.pos_start.ftxt, self.pos_start, self.pos_end
        )
        return result

    def generate_traceback(self):
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            if pos is not None:
                result = (
                    f"  Archivo {pos.fn}, línea {pos.ln + 1}, "
                    f"en {ctx.display_name}\n"
                ) + result
            else:
                result = f"  En {ctx.display_name}\n" + result

            if ctx.parent is None:
                break

            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return "Rastreo (llamadas recientes más última):\n" + result


#######################################
# POSICIÓN
#######################################


class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


#######################################
# TOKENS
#######################################

TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_STRING = "STRING"
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"

TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_MOD = "MOD"
TT_POW = "POW"

TT_EQ = "EQ"
TT_PLUSEQ = "PLUSEQ"
TT_MINUSEQ = "MINUSEQ"
TT_MULEQ = "MULEQ"
TT_DIVEQ = "DIVEQ"
TT_MODEQ = "MODEQ"

TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_LSQUARE = "LSQUARE"
TT_RSQUARE = "RSQUARE"

TT_EE = "EE"
TT_NE = "NE"
TT_LT = "LT"
TT_GT = "GT"
TT_LTE = "LTE"
TT_GTE = "GTE"

TT_COMMA = "COMMA"
TT_ARROW = "ARROW"
TT_NEWLINE = "NEWLINE"
TT_EOF = "EOF"


KEYWORDS = [
    "VAR",
    "AND",
    "OR",
    "NOT",
    "IF",
    "ELIF",
    "ELSE",
    "THEN",
    "FOR",
    "IN",
    "TO",
    "STEP",
    "WHILE",
    "FUN",
    "END",
    "RETURN",
    "CONTINUE",
    "BREAK",
    "TRUE",
    "FALSE",
    "NULL",
]


#######################################
# TOKEN
#######################################


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        self.pos_start = pos_start.copy() if pos_start else None

        if pos_start:
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value is not None:
            return f"{self.type}:{self.value}"

        return f"{self.type}"


#######################################
# LEXER
#######################################


class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)

        if self.pos.idx < len(self.text):
            self.current_char = self.text[self.pos.idx]
        else:
            self.current_char = None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:

            if self.current_char in " \t\r":
                self.advance()

            elif self.current_char == "#":
                self.skip_comment()

            elif self.current_char == "/" and self.peek() == "/":
                self.advance()
                self.advance()
                self.skip_comment()

            elif self.current_char in ";\n":
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_number())

            elif self.current_char in LETTERS or self.current_char == "_":
                tokens.append(self.make_identifier())

            elif self.current_char in ('"', "'"):
                token, error = self.make_string()

                if error:
                    return [], error

                tokens.append(token)

            elif self.current_char == "+":
                tokens.append(self.make_plus_or_pluseq())

            elif self.current_char == "-":
                tokens.append(self.make_minus_or_arrow())

            elif self.current_char == "*":
                tokens.append(self.make_mul_or_muleq())

            elif self.current_char == "/":
                tokens.append(self.make_div_or_diveq())

            elif self.current_char == "%":
                tokens.append(self.make_mod_or_modeq())

            elif self.current_char == "^":
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()

            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()

            elif self.current_char == "[":
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()

            elif self.current_char == "]":
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()

            elif self.current_char == "!":
                token, error = self.make_not_equals()

                if error:
                    return [], error

                tokens.append(token)

            elif self.current_char == "=":
                tokens.append(self.make_equals())

            elif self.current_char == "<":
                tokens.append(self.make_less_than())

            elif self.current_char == ">":
                tokens.append(self.make_greater_than())

            elif self.current_char == ",":
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()

            else:
                pos_start = self.pos.copy()
                char = self.current_char

                self.advance()

                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))

        return tokens, None

    def peek(self):
        next_idx = self.pos.idx + 1

        if next_idx >= len(self.text):
            return None

        return self.text[next_idx]

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break

                dot_count += 1

            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)

        return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_string(self):
        string_value = ""
        pos_start = self.pos.copy()
        quote = self.current_char

        self.advance()

        escape_characters = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "\\": "\\",
            '"': '"',
            "'": "'",
            "0": "\0",
        }

        while self.current_char is not None and self.current_char != quote:
            if self.current_char == "\\":
                self.advance()

                if self.current_char is None:
                    return None, ExpectedCharError(
                        pos_start, self.pos, 'Se esperaba un carácter después de "\\"'
                    )

                string_value += escape_characters.get(
                    self.current_char, self.current_char
                )

                self.advance()

            else:
                string_value += self.current_char
                self.advance()

        if self.current_char is None:
            return None, ExpectedCharError(
                pos_start, self.pos, f"Se esperaba '{quote}'"
            )

        self.advance()

        return Token(TT_STRING, string_value, pos_start, self.pos), None

    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS:
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str.upper() in KEYWORDS else TT_IDENTIFIER

        if tok_type == TT_KEYWORD:
            id_str = id_str.upper()

        return Token(tok_type, id_str, pos_start, self.pos)

    def make_plus_or_pluseq(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_PLUSEQ, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_PLUS, pos_start=pos_start, pos_end=self.pos)

    def make_minus_or_arrow(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == ">":
            self.advance()

            return Token(TT_ARROW, pos_start=pos_start, pos_end=self.pos)

        if self.current_char == "=":
            self.advance()

            return Token(TT_MINUSEQ, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_MINUS, pos_start=pos_start, pos_end=self.pos)

    def make_mul_or_muleq(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_MULEQ, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_MUL, pos_start=pos_start, pos_end=self.pos)

    def make_div_or_diveq(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_DIVEQ, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_DIV, pos_start=pos_start, pos_end=self.pos)

    def make_mod_or_modeq(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_MODEQ, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_MOD, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return (Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None)

        return None, ExpectedCharError(pos_start, self.pos, "'=' después de '!'")

    def make_equals(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_EE, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_EQ, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_LTE, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_LT, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        pos_start = self.pos.copy()

        self.advance()

        if self.current_char == "=":
            self.advance()

            return Token(TT_GTE, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_GT, pos_start=pos_start, pos_end=self.pos)

    def skip_comment(self):
        while self.current_char is not None and self.current_char != "\n":
            self.advance()


#######################################
# NODOS AST
#######################################


class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = tok.pos_start
        self.pos_end = tok.pos_end

    def __repr__(self):
        return repr(self.tok)


class StringNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = tok.pos_start
        self.pos_end = tok.pos_end

    def __repr__(self):
        return repr(self.tok)


class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'[{", ".join(map(repr, self.element_nodes))}]'


class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = var_name_tok.pos_start
        self.pos_end = var_name_tok.pos_end

    def __repr__(self):
        return repr(self.var_name_tok)


class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.pos_start = var_name_tok.pos_start
        self.pos_end = value_node.pos_end


class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = left_node.pos_start
        self.pos_end = right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, " f"{self.op_tok}, " f"{self.right_node})"


class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f"({self.op_tok}, {self.node})"


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = cases[0][0].pos_start

        if else_case:
            self.pos_end = else_case[0].pos_end
        else:
            self.pos_end = cases[-1][1].pos_end


class ForNode:
    def __init__(
        self,
        var_name_tok,
        start_value_node,
        end_value_node,
        step_value_node,
        body_node,
        should_return_null,
    ):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = var_name_tok.pos_start
        self.pos_end = body_node.pos_end


class ForInNode:
    def __init__(self, var_name_tok, iterable_node, body_node, should_return_null):
        self.var_name_tok = var_name_tok
        self.iterable_node = iterable_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = var_name_tok.pos_start
        self.pos_end = body_node.pos_end


class WhileNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = condition_node.pos_start
        self.pos_end = body_node.pos_end


class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if var_name_tok:
            self.pos_start = var_name_tok.pos_start
        elif arg_name_toks:
            self.pos_start = arg_name_toks[0].pos_start
        else:
            self.pos_start = body_node.pos_start

        self.pos_end = body_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = node_to_call.pos_start

        if arg_nodes:
            self.pos_end = arg_nodes[-1].pos_end
        else:
            self.pos_end = node_to_call.pos_end


class IndexNode:
    def __init__(self, collection_node, index_node):
        self.collection_node = collection_node
        self.index_node = index_node

        self.pos_start = collection_node.pos_start
        self.pos_end = index_node.pos_end


class IndexAssignNode:
    def __init__(self, collection_node, index_node, value_node):
        self.collection_node = collection_node
        self.index_node = index_node
        self.value_node = value_node

        self.pos_start = collection_node.pos_start
        self.pos_end = value_node.pos_end


class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end


class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


#######################################
# RESULTADO DEL PARSER
#######################################


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count

        if res.error:
            self.error = res.error

        return res.node

    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None

        return self.register(res)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error

        return self


#######################################
# PARSER
#######################################


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.current_tok = None
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.update_current_tok()
        return self.current_tok

    def reverse(self, amount=1):
        self.tok_idx -= amount

        if self.tok_idx < -1:
            self.tok_idx = -1

        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        if 0 <= self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self):
        res = self.statements()

        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "El token no puede aparecer después de los tokens anteriores",
                )
            )

        return res

    ###################################
    # STATEMENTS
    ###################################

    def statements(self):
        res = ParseResult()
        statements = []

        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type == TT_EOF:
            return res.success(ListNode([], pos_start, self.current_tok.pos_end.copy()))

        while True:
            statement = res.try_register(self.statement())

            if not statement:
                self.reverse(res.to_reverse_count)
                break

            statements.append(statement)

            newline_count = 0

            while self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1

            if newline_count == 0:
                break

            if self.current_tok.type in (TT_EOF,):
                break

        return res.success(
            ListNode(statements, pos_start, self.current_tok.pos_end.copy())
        )

    ###################################
    # STATEMENT
    ###################################

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "RETURN"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type in (TT_NEWLINE, TT_EOF):
                return res.success(
                    ReturnNode(None, pos_start, self.current_tok.pos_start.copy())
                )

            expr = res.register(self.expr())

            if res.error:
                return res

            return res.success(
                ReturnNode(expr, pos_start, self.current_tok.pos_start.copy())
            )

        if self.current_tok.matches(TT_KEYWORD, "CONTINUE"):
            res.register_advancement()
            self.advance()

            return res.success(
                ContinueNode(pos_start, self.current_tok.pos_start.copy())
            )

        if self.current_tok.matches(TT_KEYWORD, "BREAK"):
            res.register_advancement()
            self.advance()

            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        expr = res.register(self.expr())

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    (
                        "Esperando una expresión válida, "
                        "'RETURN', 'CONTINUE' o 'BREAK'"
                    ),
                )
            )

        return res.success(expr)

    ###################################
    # EXPRESIONES
    ###################################

    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, "VAR"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Identificador esperado",
                    )
                )

            var_name = self.current_tok

            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_EQ:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando '='",
                    )
                )

            res.register_advancement()
            self.advance()

            value = res.register(self.expr())

            if res.error:
                return res

            return res.success(VarAssignNode(var_name, value))

        left = res.register(
            self.bin_op(self.comp_expr, ((TT_KEYWORD, "AND"), (TT_KEYWORD, "OR")))
        )

        if res.error:
            return res

        if self.current_tok.type in (
            TT_PLUSEQ,
            TT_MINUSEQ,
            TT_MULEQ,
            TT_DIVEQ,
            TT_MODEQ,
        ):
            op_tok = self.current_tok

            res.register_advancement()
            self.advance()

            right = res.register(self.expr())

            if res.error:
                return res

            if isinstance(left, VarAccessNode):
                operator_map = {
                    TT_PLUSEQ: TT_PLUS,
                    TT_MINUSEQ: TT_MINUS,
                    TT_MULEQ: TT_MUL,
                    TT_DIVEQ: TT_DIV,
                    TT_MODEQ: TT_MOD,
                }

                fake_op = Token(
                    operator_map[op_tok.type],
                    pos_start=op_tok.pos_start,
                    pos_end=op_tok.pos_end,
                )

                value = BinOpNode(left, fake_op, right)

                return res.success(VarAssignNode(left.var_name_tok, value))

            if isinstance(left, IndexNode):
                operator_map = {
                    TT_PLUSEQ: TT_PLUS,
                    TT_MINUSEQ: TT_MINUS,
                    TT_MULEQ: TT_MUL,
                    TT_DIVEQ: TT_DIV,
                    TT_MODEQ: TT_MOD,
                }

                fake_op = Token(
                    operator_map[op_tok.type],
                    pos_start=op_tok.pos_start,
                    pos_end=op_tok.pos_end,
                )

                value = BinOpNode(left, fake_op, right)

                return res.success(
                    IndexAssignNode(left.collection_node, left.index_node, value)
                )

            return res.failure(
                InvalidSyntaxError(
                    op_tok.pos_start,
                    op_tok.pos_end,
                    "El operador de asignación requiere una variable o un índice",
                )
            )

        if self.current_tok.type == TT_EQ:
            eq_tok = self.current_tok

            res.register_advancement()
            self.advance()

            value = res.register(self.expr())

            if res.error:
                return res

            if isinstance(left, VarAccessNode):
                return res.success(VarAssignNode(left.var_name_tok, value))

            if isinstance(left, IndexNode):
                return res.success(
                    IndexAssignNode(left.collection_node, left.index_node, value)
                )

            return res.failure(
                InvalidSyntaxError(
                    eq_tok.pos_start,
                    eq_tok.pos_end,
                    "Solo se pueden asignar valores a variables o índices",
                )
            )

        return res.success(left)

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, "NOT"):
            op_tok = self.current_tok

            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())

            if res.error:
                return res

            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(
            self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE))
        )

        if res.error:
            return res

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()

            factor = res.register(self.factor())

            if res.error:
                return res

            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (TT_POW,), self.factor)

    ###################################
    # CALL / INDEX
    ###################################

    def call(self):
        res = ParseResult()

        atom = res.register(self.atom())

        if res.error:
            return res

        while True:

            if self.current_tok.type == TT_LPAREN:
                res.register_advancement()
                self.advance()

                arg_nodes = []

                if self.current_tok.type == TT_RPAREN:
                    res.register_advancement()
                    self.advance()

                else:
                    arg_nodes.append(res.register(self.expr()))

                    if res.error:
                        return res

                    while self.current_tok.type == TT_COMMA:
                        res.register_advancement()
                        self.advance()

                        arg_nodes.append(res.register(self.expr()))

                        if res.error:
                            return res

                    if self.current_tok.type != TT_RPAREN:
                        return res.failure(
                            InvalidSyntaxError(
                                self.current_tok.pos_start,
                                self.current_tok.pos_end,
                                "Esperando ',' o ')'",
                            )
                        )

                    res.register_advancement()
                    self.advance()

                atom = CallNode(atom, arg_nodes)

                continue

            if self.current_tok.type == TT_LSQUARE:
                res.register_advancement()
                self.advance()

                index_node = res.register(self.expr())

                if res.error:
                    return res

                if self.current_tok.type != TT_RSQUARE:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Esperando ']'",
                        )
                    )

                res.register_advancement()
                self.advance()

                atom = IndexNode(atom, index_node)

                continue

            break

        return res.success(atom)

    ###################################
    # ATOM
    ###################################


    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()

            return res.success(NumberNode(tok))

        if tok.type == TT_STRING:
            res.register_advancement()
            self.advance()

            return res.success(StringNode(tok))

        if tok.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()

            return res.success(VarAccessNode(tok))

        if tok.matches(TT_KEYWORD, "TRUE"):
            res.register_advancement()
            self.advance()

            return res.success(NumberNode(Token(TT_INT, 1, tok.pos_start, tok.pos_end)))

        if tok.matches(TT_KEYWORD, "FALSE"):
            res.register_advancement()
            self.advance()

            return res.success(NumberNode(Token(TT_INT, 0, tok.pos_start, tok.pos_end)))

        if tok.matches(TT_KEYWORD, "NULL"):
            res.register_advancement()
            self.advance()

            return res.success(NumberNode(Token(TT_INT, 0, tok.pos_start, tok.pos_end)))

        if tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())

            if res.error:
                return res

            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando ')'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success(expr)

        if tok.type == TT_LSQUARE:
            list_res = self.list_expr()

            if list_res.error:
                return list_res

            res.register(list_res)
            return res.success(list_res.node)

        if tok.matches(TT_KEYWORD, "IF"):
            if_res = self.if_expr()

            if if_res.error:
                return if_res

            res.register(if_res)
            return res.success(if_res.node)

        if tok.matches(TT_KEYWORD, "FOR"):
            for_res = self.for_expr()

            if for_res.error:
                return for_res

            res.register(for_res)
            return res.success(for_res.node)

        if tok.matches(TT_KEYWORD, "WHILE"):
            while_res = self.while_expr()

            if while_res.error:
                return while_res

            res.register(while_res)
            return res.success(while_res.node)

        if tok.matches(TT_KEYWORD, "FUN"):
            fun_res = self.func_def()

            if fun_res.error:
                return fun_res

            res.register(fun_res)
            return res.success(fun_res.node)

        return res.failure(
            InvalidSyntaxError(
                tok.pos_start,
                tok.pos_end,
                (
                    "Esperando número, cadena, "
                    "identificador, TRUE, FALSE, NULL, "
                    "'+', '-', '(', '[', 'IF', 'FOR', "
                    "'WHILE', 'FUN' o 'NOT'"
                ),
            )
        )

    ###################################
    # LISTAS
    ###################################

    def list_expr(self):
        res = ParseResult()

        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando '['",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()

            return res.success(
                ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy())
            )

        element_nodes.append(res.register(self.expr()))

        if res.error:
            return res

        while self.current_tok.type == TT_COMMA:
            res.register_advancement()
            self.advance()

            element_nodes.append(res.register(self.expr()))

            if res.error:
                return res

        if self.current_tok.type != TT_RSQUARE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando ',' o ']'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy())
        )

    ###################################
    # IF
    ###################################

    def if_expr(self):
        res = ParseResult()

        all_cases = res.register(self.if_expr_cases("IF"))

        if res.error:
            return res

        cases, else_case = all_cases

        return res.success(IfNode(cases, else_case))

    def if_expr_cases(self, case_keyword):
        res = ParseResult()

        cases = []
        else_case = None

        if not self.current_tok.matches(TT_KEYWORD, case_keyword):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    f"Esperando '{case_keyword}'",
                )
            )

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())

        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, "THEN"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'THEN'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())

            if res.error:
                return res

            cases.append((condition, body, True))

            if self.current_tok.matches(TT_KEYWORD, "END"):
                res.register_advancement()
                self.advance()

            else:
                if self.current_tok.matches(TT_KEYWORD, "ELIF"):
                    more = res.register(self.if_expr_cases("ELIF"))

                    if res.error:
                        return res

                    new_cases, else_case = more
                    cases.extend(new_cases)

                elif self.current_tok.matches(TT_KEYWORD, "ELSE"):
                    else_case = res.register(self.if_expr_c())

                    if res.error:
                        return res

        else:
            expr = res.register(self.statement())

            if res.error:
                return res

            cases.append((condition, expr, False))

            if self.current_tok.matches(TT_KEYWORD, "ELIF"):
                more = res.register(self.if_expr_cases("ELIF"))

                if res.error:
                    return res

                new_cases, else_case = more
                cases.extend(new_cases)

            elif self.current_tok.matches(TT_KEYWORD, "ELSE"):
                else_case = res.register(self.if_expr_c())

                if res.error:
                    return res

        return res.success((cases, else_case))

    def if_expr_c(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "ELSE"):
            return res.success(None)

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())

            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, "END"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando 'END'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success((body, True))

        body = res.register(self.statement())

        if res.error:
            return res

        return res.success((body, False))

    ###################################
    # FOR
    ###################################

    def for_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "FOR"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'FOR'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando identificador",
                )
            )

        var_name = self.current_tok

        res.register_advancement()
        self.advance()

        if self.current_tok.matches(TT_KEYWORD, "IN"):
            res.register_advancement()
            self.advance()

            iterable = res.register(self.expr())

            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, "THEN"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando 'THEN'",
                    )
                )

            res.register_advancement()
            self.advance()

            if self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()

                body = res.register(self.statements())

                if res.error:
                    return res

                if not self.current_tok.matches(TT_KEYWORD, "END"):
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Esperando 'END'",
                        )
                    )

                res.register_advancement()
                self.advance()

                return res.success(ForInNode(var_name, iterable, body, True))

            body = res.register(self.statement())

            if res.error:
                return res

            return res.success(ForInNode(var_name, iterable, body, False))

        if self.current_tok.type != TT_EQ:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando '='",
                )
            )

        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())

        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, "TO"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'TO'",
                )
            )

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())

        if res.error:
            return res

        step_value = None

        if self.current_tok.matches(TT_KEYWORD, "STEP"):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())

            if res.error:
                return res

        if not self.current_tok.matches(TT_KEYWORD, "THEN"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'THEN'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())

            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, "END"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando 'END'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success(
                ForNode(var_name, start_value, end_value, step_value, body, True)
            )

        body = res.register(self.statement())

        if res.error:
            return res

        return res.success(
            ForNode(var_name, start_value, end_value, step_value, body, False)
        )

    ###################################
    # WHILE
    ###################################

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "WHILE"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'WHILE'",
                )
            )

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())

        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, "THEN"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'THEN'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())

            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, "END"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Esperando 'END'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success(WhileNode(condition, body, True))

        body = res.register(self.statement())

        if res.error:
            return res

        return res.success(WhileNode(condition, body, False))

    ###################################
    # FUNCIONES
    ###################################

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "FUN"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'FUN'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok

            res.register_advancement()
            self.advance()

        else:
            var_name_tok = None

        if self.current_tok.type != TT_LPAREN:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando '('",
                )
            )

        res.register_advancement()
        self.advance()

        arg_name_toks = []

        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)

            res.register_advancement()
            self.advance()

            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Identificador esperado",
                        )
                    )

                arg_name_toks.append(self.current_tok)

                res.register_advancement()
                self.advance()

        if self.current_tok.type != TT_RPAREN:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando ')'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_ARROW:
            res.register_advancement()
            self.advance()

            body = res.register(self.expr())

            if res.error:
                return res

            return res.success(FuncDefNode(var_name_tok, arg_name_toks, body, True))

        if self.current_tok.type != TT_NEWLINE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando '->' o una nueva línea",
                )
            )

        res.register_advancement()
        self.advance()

        body = res.register(self.statements())

        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, "END"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Esperando 'END'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(FuncDefNode(var_name_tok, arg_name_toks, body, False))

    ###################################
    # OPERADORES
    ###################################

    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a

        res = ParseResult()

        left = res.register(func_a())

        if res.error:
            return res

        while (
            self.current_tok.type in ops
            or (self.current_tok.type, self.current_tok.value) in ops
        ):
            op_tok = self.current_tok

            res.register_advancement()
            self.advance()

            right = res.register(func_b())

            if res.error:
                return res

            left = BinOpNode(left, op_tok, right)

        return res.success(left)


#######################################
# RESULTADO DEL RUNTIME
#######################################


class RTResult:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False

    def register(self, res):
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break

        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        return (
            self.error is not None
            or self.func_return_value is not None
            or self.loop_should_continue
            or self.loop_should_break
        )


#######################################
# VALORES
#######################################


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        return None, self.illegal_operation(other)

    def multed_by(self, other):
        return None, self.illegal_operation(other)

    def dived_by(self, other):
        return None, self.illegal_operation(other)

    def modded_by(self, other):
        return None, self.illegal_operation(other)

    def powed_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def anded_by(self, other):
        return None, self.illegal_operation(other)

    def ored_by(self, other):
        return None, self.illegal_operation(other)

    def notted(self):
        return (Number(0 if self.is_true() else 1).set_context(self.context), None)

    def execute(self, args):
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception("Sin método de copia definido")

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if other is None:
            other = self

        return RTError(self.pos_start, other.pos_end, "Operación ilegal", self.context)


#######################################
# NUMBER
#######################################


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return (Number(self.value + other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return (Number(self.value - other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return (Number(self.value * other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def dived_by(self, other):
        if not isinstance(other, Number):
            return None, self.illegal_operation(other)

        if other.value == 0:
            return None, RTError(
                other.pos_start, other.pos_end, "División por cero", self.context
            )

        return (Number(self.value / other.value).set_context(self.context), None)

    def modded_by(self, other):
        if not isinstance(other, Number):
            return None, self.illegal_operation(other)

        if other.value == 0:
            return None, RTError(
                other.pos_start, other.pos_end, "Módulo por cero", self.context
            )

        return (Number(self.value % other.value).set_context(self.context), None)

    def powed_by(self, other):
        if not isinstance(other, Number):
            return None, self.illegal_operation(other)

        try:
            value = self.value**other.value
        except Exception:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "No se pudo calcular la potencia",
                self.context,
            )

        return (Number(value).set_context(self.context), None)

    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value < other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value > other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def anded_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.is_true() and other.is_true())).set_context(
                    self.context
                ),
                None,
            )

        return None, self.illegal_operation(other)

    def ored_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.is_true() or other.is_true())).set_context(
                    self.context
                ),
                None,
            )

        return None, self.illegal_operation(other)

    def notted(self):
        return (Number(0 if self.is_true() else 1).set_context(self.context), None)

    def copy(self):
        copy = Number(self.value)

        copy.set_pos(self.pos_start, self.pos_end)

        copy.set_context(self.context)

        return copy

    def is_true(self):
        return self.value != 0

    def __str__(self):
        if isinstance(self.value, float):
            if self.value.is_integer():
                return str(int(self.value))

        return str(self.value)

    def __repr__(self):
        return self.__str__()


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)


#######################################
# STRING
#######################################


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return (String(self.value + other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            if not isinstance(other.value, int):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "La cantidad de repetición debe ser un entero",
                    self.context,
                )

            return (String(self.value * other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )

        return None, self.illegal_operation(other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)

        copy.set_pos(self.pos_start, self.pos_end)

        copy.set_context(self.context)

        return copy

    def __str__(self):
        return self.value

    def __repr__(self):
        escaped = (
            self.value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )

        return f'"{escaped}"'


#######################################
# LIST
#######################################


class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def added_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def subbed_by(self, other):
        if not isinstance(other, Number):
            return None, self.illegal_operation(other)

        if not isinstance(other.value, int):
            return None, RTError(
                other.pos_start,
                other.pos_end,
                "El índice debe ser un número entero",
                self.context,
            )

        new_list = self.copy()

        try:
            new_list.elements.pop(other.value)
        except IndexError:
            return None, RTError(
                other.pos_start,
                other.pos_end,
                "Índice fuera de los límites de la lista",
                self.context,
            )

        return new_list, None

    def multed_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)

            return new_list, None

        if isinstance(other, Number):
            if not isinstance(other.value, int):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "La cantidad de repetición debe ser un entero",
                    self.context,
                )

            return (List(self.elements * other.value).set_context(self.context), None)

        return None, self.illegal_operation(other)

    def dived_by(self, other):
        if not isinstance(other, Number):
            return None, self.illegal_operation(other)

        if not isinstance(other.value, int):
            return None, RTError(
                other.pos_start,
                other.pos_end,
                "El índice debe ser un número entero",
                self.context,
            )

        try:
            return (self.elements[other.value], None)
        except IndexError:
            return None, RTError(
                other.pos_start,
                other.pos_end,
                "Índice fuera de los límites de la lista",
                self.context,
            )

    def get_comparison_eq(self, other):
        if not isinstance(other, List):
            return None, self.illegal_operation(other)

        if len(self.elements) != len(other.elements):
            return (Number.false.set_context(self.context), None)

        for a, b in zip(self.elements, other.elements):
            if type(a) != type(b) or str(a) != str(b):
                return (Number.false.set_context(self.context), None)

        return (Number.true.set_context(self.context), None)

    def get_comparison_ne(self, other):
        result, error = self.get_comparison_eq(other)

        if error:
            return None, error

        return (Number(0 if result.value else 1).set_context(self.context), None)

    def copy(self):
        copy = List(self.elements.copy())

        copy.set_pos(self.pos_start, self.pos_end)

        copy.set_context(self.context)

        return copy

    def is_true(self):
        return len(self.elements) > 0

    def __str__(self):
        return ", ".join(str(x) for x in self.elements)

    def __repr__(self):
        return "[" + ", ".join(repr(x) for x in self.elements) + "]"


#######################################
# FUNCIONES
#######################################


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)

        if self.context:
            parent_table = self.context.symbol_table
        else:
            parent_table = None

        new_context.symbol_table = SymbolTable(parent_table)

        return new_context

    def check_args(self, arg_names, args):
        res = RTResult()

        if len(args) > len(arg_names):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    (
                        f"Se pasaron "
                        f"{len(args) - len(arg_names)} "
                        f"argumentos de más a {self}"
                    ),
                    self.context,
                )
            )

        if len(args) < len(arg_names):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    (
                        f"Faltan "
                        f"{len(arg_names) - len(args)} "
                        f"argumentos para {self}"
                    ),
                    self.context,
                )
            )

        return res.success(None)

    def populate_args(self, arg_names, args, exec_ctx):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]

            arg_value.set_context(exec_ctx)

            exec_ctx.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()

        res.register(self.check_args(arg_names, args))

        if res.should_return():
            return res

        self.populate_args(arg_names, args, exec_ctx)

        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)

        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return

    def execute(self, args):
        res = RTResult()

        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))

        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))

        if res.should_return() and res.func_return_value is None:
            return res

        ret_value = (
            (value if self.should_auto_return else None)
            or res.func_return_value
            or Number.null
        )

        return res.success(ret_value)

    def copy(self):
        copy = Function(
            self.name, self.body_node, self.arg_names, self.should_auto_return
        )

        copy.set_context(self.context)

        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<function {self.name}>"


#######################################
# FUNCIONES BUILT-IN
#######################################


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RTResult()

        exec_ctx = self.generate_new_context()

        method_name = f"execute_{self.name}"

        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))

        if res.should_return():
            return res

        return_value = res.register(method(exec_ctx))

        if res.should_return():
            return res

        return res.success(return_value)

    def no_visit_method(self, context):
        raise Exception(f"No execute_{self.name} method defined")

    def copy(self):
        copy = BuiltInFunction(self.name)

        copy.set_context(self.context)

        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"

    ###################################
    # PRINT
    ###################################

    def execute_print(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        print(str(value))

        return RTResult().success(Number.null)

    execute_print.arg_names = ["value"]

    ###################################

    def execute_print_ret(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(String(str(value)))

    execute_print_ret.arg_names = ["value"]

    ###################################
    # INPUT
    ###################################

    def execute_input(self, exec_ctx):
        try:
            text = input()
        except EOFError:
            text = ""

        return RTResult().success(String(text))

    execute_input.arg_names = []

    ###################################

    def execute_input_int(self, exec_ctx):
        while True:
            try:
                text = input()
                number = int(text)
                break

            except ValueError:
                print(f"'{text}' debe ser un entero. " f"Inténtalo de nuevo.")

            except EOFError:
                return RTResult().success(Number(0))

        return RTResult().success(Number(number))

    execute_input_int.arg_names = []

    ###################################
    # CLEAR
    ###################################

    def execute_clear(self, exec_ctx):
        os.system("cls" if os.name == "nt" else "clear")

        return RTResult().success(Number.null)

    execute_clear.arg_names = []

    ###################################
    # TIPOS
    ###################################

    def execute_is_number(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(
            Number.true if isinstance(value, Number) else Number.false
        )

    execute_is_number.arg_names = ["value"]

    ###################################

    def execute_is_string(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(
            Number.true if isinstance(value, String) else Number.false
        )

    execute_is_string.arg_names = ["value"]

    ###################################

    def execute_is_list(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(
            Number.true if isinstance(value, List) else Number.false
        )

    execute_is_list.arg_names = ["value"]

    ###################################

    def execute_is_function(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(
            Number.true if isinstance(value, BaseFunction) else Number.false
        )

    execute_is_function.arg_names = ["value"]

    ###################################
    # TYPE
    ###################################

    def execute_type(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        if isinstance(value, Number):
            if value.value == 0:
                name = "number"
            else:
                name = "number"

        elif isinstance(value, String):
            name = "string"

        elif isinstance(value, List):
            name = "list"

        elif isinstance(value, BaseFunction):
            name = "function"

        else:
            name = "unknown"

        return RTResult().success(String(name))

    execute_type.arg_names = ["value"]

    ###################################
    # STRING
    ###################################

    def execute_str(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(String(str(value)))

    execute_str.arg_names = ["value"]

    ###################################
    # NUMBER
    ###################################

    def execute_num(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        if isinstance(value, Number):
            return RTResult().success(value.copy())

        if isinstance(value, String):
            try:
                text = value.value.strip()

                if "." in text:
                    number = float(text)
                else:
                    number = int(text)

                return RTResult().success(Number(number))

            except ValueError:
                return RTResult().failure(
                    RTError(
                        value.pos_start,
                        value.pos_end,
                        f"'{value.value}' no es un número válido",
                        exec_ctx,
                    )
                )

        return RTResult().failure(
            RTError(
                self.pos_start,
                self.pos_end,
                "El valor no puede convertirse a número",
                exec_ctx,
            )
        )

    execute_num.arg_names = ["value"]

    ###################################
    # LISTAS
    ###################################

    def execute_append(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")

        value = exec_ctx.symbol_table.get("value")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El primer argumento debe ser una lista",
                    exec_ctx,
                )
            )

        list_.elements.append(value)

        return RTResult().success(Number.null)

    execute_append.arg_names = ["list", "value"]

    ###################################

    def execute_pop(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")

        index = exec_ctx.symbol_table.get("index")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El primer argumento debe ser una lista",
                    exec_ctx,
                )
            )

        if not isinstance(index, Number):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El índice debe ser un número",
                    exec_ctx,
                )
            )

        if not isinstance(index.value, int):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El índice debe ser un entero",
                    exec_ctx,
                )
            )

        try:
            element = list_.elements.pop(index.value)

        except IndexError:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Índice fuera de los límites de la lista",
                    exec_ctx,
                )
            )

        return RTResult().success(element)

    execute_pop.arg_names = ["list", "index"]

    ###################################

    def execute_extend(self, exec_ctx):
        list_a = exec_ctx.symbol_table.get("listA")

        list_b = exec_ctx.symbol_table.get("listB")

        if not isinstance(list_a, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El primer argumento debe ser una lista",
                    exec_ctx,
                )
            )

        if not isinstance(list_b, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "El segundo argumento debe ser una lista",
                    exec_ctx,
                )
            )

        list_a.elements.extend(list_b.elements)

        return RTResult().success(Number.null)

    execute_extend.arg_names = ["listA", "listB"]

    ###################################

    def execute_len(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        if isinstance(value, List):
            length = len(value.elements)

        elif isinstance(value, String):
            length = len(value.value)

        else:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "LEN solo acepta listas o cadenas",
                    exec_ctx,
                )
            )

        return RTResult().success(Number(length))

    execute_len.arg_names = ["value"]

    ###################################
    # RANGE
    ###################################

    def execute_range(self, exec_ctx):
        start = exec_ctx.symbol_table.get("start")

        end = exec_ctx.symbol_table.get("end")

        step = exec_ctx.symbol_table.get("step")

        for value in (start, end, step):
            if not isinstance(value, Number):
                return RTResult().failure(
                    RTError(
                        self.pos_start, self.pos_end, "RANGE requiere números", exec_ctx
                    )
                )

        if not isinstance(start.value, int):
            return RTResult().failure(
                RTError(
                    start.pos_start,
                    start.pos_end,
                    "El inicio de RANGE debe ser entero",
                    exec_ctx,
                )
            )

        if not isinstance(end.value, int):
            return RTResult().failure(
                RTError(
                    end.pos_start,
                    end.pos_end,
                    "El final de RANGE debe ser entero",
                    exec_ctx,
                )
            )

        if not isinstance(step.value, int):
            return RTResult().failure(
                RTError(
                    step.pos_start,
                    step.pos_end,
                    "El paso de RANGE debe ser entero",
                    exec_ctx,
                )
            )

        if step.value == 0:
            return RTResult().failure(
                RTError(
                    step.pos_start,
                    step.pos_end,
                    "El paso de RANGE no puede ser cero",
                    exec_ctx,
                )
            )

        values = [Number(i) for i in range(start.value, end.value, step.value)]

        return RTResult().success(List(values))

    execute_range.arg_names = ["start", "end", "step"]

    ###################################
    # ABS
    ###################################

    def execute_abs(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(value, Number):
            return RTResult().failure(
                RTError(
                    self.pos_start, self.pos_end, "ABS requiere un número", exec_ctx
                )
            )

        return RTResult().success(Number(abs(value.value)))

    execute_abs.arg_names = ["value"]

    ###################################
    # MIN
    ###################################

    def execute_min(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start, self.pos_end, "MIN requiere una lista", exec_ctx
                )
            )

        if not list_.elements:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "MIN no puede trabajar con una lista vacía",
                    exec_ctx,
                )
            )

        if not all(isinstance(x, Number) for x in list_.elements):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "MIN requiere una lista de números",
                    exec_ctx,
                )
            )

        return RTResult().success(Number(min(x.value for x in list_.elements)))

    execute_min.arg_names = ["list"]

    ###################################
    # MAX
    ###################################

    def execute_max(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start, self.pos_end, "MAX requiere una lista", exec_ctx
                )
            )

        if not list_.elements:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "MAX no puede trabajar con una lista vacía",
                    exec_ctx,
                )
            )

        if not all(isinstance(x, Number) for x in list_.elements):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "MAX requiere una lista de números",
                    exec_ctx,
                )
            )

        return RTResult().success(Number(max(x.value for x in list_.elements)))

    execute_max.arg_names = ["list"]

    ###################################
    # SLEEP
    ###################################

    def execute_sleep(self, exec_ctx):
        seconds = exec_ctx.symbol_table.get("seconds")

        if not isinstance(seconds, Number):
            return RTResult().failure(
                RTError(
                    self.pos_start, self.pos_end, "SLEEP requiere un número", exec_ctx
                )
            )

        if seconds.value < 0:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "SLEEP no acepta valores negativos",
                    exec_ctx,
                )
            )

        time.sleep(seconds.value)

        return RTResult().success(Number.null)

    execute_sleep.arg_names = ["seconds"]

    ###################################
    # ASSERT
    ###################################

    def execute_assert(self, exec_ctx):
        condition = exec_ctx.symbol_table.get("condition")

        message = exec_ctx.symbol_table.get("message")

        if not condition.is_true():
            return RTResult().failure(
                RTError(self.pos_start, self.pos_end, str(message), exec_ctx)
            )

        return RTResult().success(Number.null)

    execute_assert.arg_names = ["condition", "message"]

    ###################################
    # RUN
    ###################################

    def execute_run(self, exec_ctx):
        fn = exec_ctx.symbol_table.get("fn")

        if not isinstance(fn, String):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "RUN requiere una cadena con el nombre del archivo",
                    exec_ctx,
                )
            )

        filename = fn.value

        try:
            with open(filename, "r", encoding="utf-8") as file:
                script = file.read()

        except Exception as error:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    (f'No se pudo abrir "{filename}"\n' f"{error}"),
                    exec_ctx,
                )
            )

        _, error = run(filename, script)

        if error:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    (f'No se pudo ejecutar "{filename}"\n\n' f"{error.as_string()}"),
                    exec_ctx,
                )
            )

        return RTResult().success(Number.null)

    execute_run.arg_names = ["fn"]


#######################################
# INSTANCIAS BUILT-IN
#######################################

BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")

BuiltInFunction.is_number = BuiltInFunction("is_number")

BuiltInFunction.is_string = BuiltInFunction("is_string")

BuiltInFunction.is_list = BuiltInFunction("is_list")

BuiltInFunction.is_function = BuiltInFunction("is_function")

BuiltInFunction.type = BuiltInFunction("type")

BuiltInFunction.str = BuiltInFunction("str")

BuiltInFunction.num = BuiltInFunction("num")

BuiltInFunction.append = BuiltInFunction("append")

BuiltInFunction.pop = BuiltInFunction("pop")

BuiltInFunction.extend = BuiltInFunction("extend")

BuiltInFunction.len = BuiltInFunction("len")

BuiltInFunction.range = BuiltInFunction("range")

BuiltInFunction.abs = BuiltInFunction("abs")

BuiltInFunction.min = BuiltInFunction("min")

BuiltInFunction.max = BuiltInFunction("max")

BuiltInFunction.sleep = BuiltInFunction("sleep")

BuiltInFunction.assert_ = BuiltInFunction("assert")

BuiltInFunction.run = BuiltInFunction("run")


#######################################
# CONTEXTO
#######################################


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


#######################################
# TABLA DE SÍMBOLOS
#######################################


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)

        if value is None and self.parent:
            return self.parent.get(name)

        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        if name in self.symbols:
            del self.symbols[name]


#######################################
# INTERPRETER
#######################################


class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"

        method = getattr(self, method_name, self.no_visit_method)

        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    ###################################
    # NUMBER
    ###################################

    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    ###################################
    # STRING
    ###################################

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    ###################################
    # LIST
    ###################################

    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))

            if res.should_return():
                return res

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    ###################################
    # VARIABLE
    ###################################

    def visit_VarAccessNode(self, node, context):
        res = RTResult()

        var_name = node.var_name_tok.value

        value = context.symbol_table.get(var_name)

        if value is None:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"'{var_name}' no está definido",
                    context,
                )
            )

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)

        return res.success(value)

    ###################################
    # ASIGNACIÓN
    ###################################

    def visit_VarAssignNode(self, node, context):
        res = RTResult()

        var_name = node.var_name_tok.value

        value = res.register(self.visit(node.value_node, context))

        if res.should_return():
            return res

        context.symbol_table.set(var_name, value)

        return res.success(value)

    ###################################
    # BINARIO
    ###################################

    def visit_BinOpNode(self, node, context):
        res = RTResult()

        left = res.register(self.visit(node.left_node, context))

        if res.should_return():
            return res

        if node.op_tok.matches(TT_KEYWORD, "AND"):
            if not left.is_true():
                return res.success(Number.false)

        elif node.op_tok.matches(TT_KEYWORD, "OR"):
            if left.is_true():
                return res.success(Number.true)

        right = res.register(self.visit(node.right_node, context))

        if res.should_return():
            return res

        op = node.op_tok

        if op.type == TT_PLUS:
            result, error = left.added_to(right)

        elif op.type == TT_MINUS:
            result, error = left.subbed_by(right)

        elif op.type == TT_MUL:
            result, error = left.multed_by(right)

        elif op.type == TT_DIV:
            result, error = left.dived_by(right)

        elif op.type == TT_MOD:
            result, error = left.modded_by(right)

        elif op.type == TT_POW:
            result, error = left.powed_by(right)

        elif op.type == TT_EE:
            result, error = left.get_comparison_eq(right)

        elif op.type == TT_NE:
            result, error = left.get_comparison_ne(right)

        elif op.type == TT_LT:
            result, error = left.get_comparison_lt(right)

        elif op.type == TT_GT:
            result, error = left.get_comparison_gt(right)

        elif op.type == TT_LTE:
            result, error = left.get_comparison_lte(right)

        elif op.type == TT_GTE:
            result, error = left.get_comparison_gte(right)

        elif op.matches(TT_KEYWORD, "AND"):
            result, error = left.anded_by(right)

        elif op.matches(TT_KEYWORD, "OR"):
            result, error = left.ored_by(right)

        else:
            return res.failure(
                RTError(op.pos_start, op.pos_end, "Operador no reconocido", context)
            )

        if error:
            return res.failure(error)

        return res.success(
            result.set_pos(node.pos_start, node.pos_end).set_context(context)
        )

    ###################################
    # UNARIO
    ###################################

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()

        value = res.register(self.visit(node.node, context))

        if res.should_return():
            return res

        if node.op_tok.type == TT_MINUS:
            result, error = value.multed_by(Number(-1))

        elif node.op_tok.type == TT_PLUS:
            result, error = value

            if error is None:
                error = None

        elif node.op_tok.matches(TT_KEYWORD, "NOT"):
            result, error = value.notted()

        else:
            return res.failure(
                RTError(
                    node.op_tok.pos_start,
                    node.op_tok.pos_end,
                    "Operador unario inválido",
                    context,
                )
            )

        if error:
            return res.failure(error)

        return res.success(result.set_pos(node.pos_start, node.pos_end))

    ###################################
    # INDEX
    ###################################

    def visit_IndexNode(self, node, context):
        res = RTResult()

        collection = res.register(self.visit(node.collection_node, context))

        if res.should_return():
            return res

        index = res.register(self.visit(node.index_node, context))

        if res.should_return():
            return res

        if not isinstance(index, Number):
            return res.failure(
                RTError(
                    node.index_node.pos_start,
                    node.index_node.pos_end,
                    "El índice debe ser un número entero",
                    context,
                )
            )

        if not isinstance(index.value, int):
            return res.failure(
                RTError(
                    node.index_node.pos_start,
                    node.index_node.pos_end,
                    "El índice debe ser un número entero",
                    context,
                )
            )

        if isinstance(collection, List):
            try:
                value = collection.elements[index.value]

            except IndexError:
                return res.failure(
                    RTError(
                        node.index_node.pos_start,
                        node.index_node.pos_end,
                        "Índice fuera de los límites de la lista",
                        context,
                    )
                )

            return res.success(
                value.copy().set_context(context).set_pos(node.pos_start, node.pos_end)
            )

        if isinstance(collection, String):
            try:
                return res.success(
                    String(collection.value[index.value])
                    .set_context(context)
                    .set_pos(node.pos_start, node.pos_end)
                )

            except IndexError:
                return res.failure(
                    RTError(
                        node.index_node.pos_start,
                        node.index_node.pos_end,
                        "Índice fuera de los límites de la cadena",
                        context,
                    )
                )

        return res.failure(
            RTError(
                node.collection_node.pos_start,
                node.collection_node.pos_end,
                "El valor no admite acceso mediante índice",
                context,
            )
        )

    ###################################
    # ASIGNACIÓN DE ÍNDICE
    ###################################

    def visit_IndexAssignNode(self, node, context):
        res = RTResult()

        # Para asignaciones directas como lista[índice] = valor,
        # usamos la lista almacenada en la tabla de símbolos en lugar
        # de la copia que devuelve visit_VarAccessNode().
        if isinstance(node.collection_node, VarAccessNode):
            collection = context.symbol_table.get(node.collection_node.var_name_tok.value)

            if collection is None:
                return res.failure(
                    RTError(
                        node.collection_node.pos_start,
                        node.collection_node.pos_end,
                        f"'{node.collection_node.var_name_tok.value}' no está definido",
                        context,
                    )
                )
        else:
            collection = res.register(self.visit(node.collection_node, context))

            if res.should_return():
                return res

        index = res.register(self.visit(node.index_node, context))

        if res.should_return():
            return res

        value = res.register(self.visit(node.value_node, context))

        if res.should_return():
            return res

        if not isinstance(index, Number):
            return res.failure(
                RTError(
                    node.index_node.pos_start,
                    node.index_node.pos_end,
                    "El índice debe ser un número entero",
                    context,
                )
            )

        if not isinstance(index.value, int):
            return res.failure(
                RTError(
                    node.index_node.pos_start,
                    node.index_node.pos_end,
                    "El índice debe ser un número entero",
                    context,
                )
            )

        if not isinstance(collection, List):
            return res.failure(
                RTError(
                    node.collection_node.pos_start,
                    node.collection_node.pos_end,
                    "Solo se pueden modificar índices de listas",
                    context,
                )
            )

        try:
            collection.elements[index.value] = value

        except IndexError:
            return res.failure(
                RTError(
                    node.index_node.pos_start,
                    node.index_node.pos_end,
                    "Índice fuera de los límites de la lista",
                    context,
                )
            )

        return res.success(value)

    ###################################
    # IF
    ###################################

    def visit_IfNode(self, node, context):
        res = RTResult()

        for (condition, expr, should_return_null) in node.cases:

            condition_value = res.register(self.visit(condition, context))

            if res.should_return():
                return res

            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))

                if res.should_return():
                    return res

                return res.success(Number.null if should_return_null else expr_value)

        if node.else_case:
            expr, should_return_null = node.else_case

            expr_value = res.register(self.visit(expr, context))

            if res.should_return():
                return res

            return res.success(Number.null if should_return_null else expr_value)

        return res.success(Number.null)

    ###################################
    # FOR
    ###################################

    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))

        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_value_node, context))

        if res.should_return():
            return res

        if not isinstance(start_value, Number) or not isinstance(end_value, Number):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "FOR requiere valores numéricos",
                    context,
                )
            )

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))

            if res.should_return():
                return res

        else:
            step_value = Number(1)

        if not isinstance(step_value, Number):
            return res.failure(
                RTError(node.pos_start, node.pos_end, "STEP debe ser numérico", context)
            )

        if step_value.value == 0:
            return res.failure(
                RTError(node.pos_start, node.pos_end, "STEP no puede ser cero", context)
            )

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(
                node.var_name_tok.value,
                Number(i).set_context(context).set_pos(node.pos_start, node.pos_end),
            )

            i += step_value.value

            value = res.register(self.visit(node.body_node, context))

            if (
                res.should_return()
                and not res.loop_should_continue
                and not res.loop_should_break
            ):
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        if node.should_return_null:
            return res.success(Number.null)

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ForInNode(self, node, context):
        res = RTResult()
        elements = []

        iterable = res.register(self.visit(node.iterable_node, context))

        if res.should_return():
            return res

        if not isinstance(iterable, List):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "FOR ... IN requiere una lista",
                    context,
                )
            )

        for item in iterable.elements:
            context.symbol_table.set(
                node.var_name_tok.value,
                item.copy().set_context(context),
            )

            value = res.register(self.visit(node.body_node, context))

            if (
                res.should_return()
                and not res.loop_should_continue
                and not res.loop_should_break
            ):
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        if node.should_return_null:
            return res.success(Number.null)

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    ###################################
    # WHILE
    ###################################

    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))

            if res.should_return():
                return res

            if not condition.is_true():
                break

            value = res.register(self.visit(node.body_node, context))

            if (
                res.should_return()
                and not res.loop_should_continue
                and not res.loop_should_break
            ):
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        if node.should_return_null:
            return res.success(Number.null)

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    ###################################
    # FUNCIÓN
    ###################################

    def visit_FuncDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None

        arg_names = [arg.value for arg in node.arg_name_toks]

        func_value = Function(
            func_name, node.body_node, arg_names, node.should_auto_return
        )

        func_value.set_context(context)

        func_value.set_pos(node.pos_start, node.pos_end)

        if func_name:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    ###################################
    # CALL
    ###################################

    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))

        if res.should_return():
            return res

        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))

            if res.should_return():
                return res

        return_value = res.register(value_to_call.execute(args))

        if res.should_return():
            return res

        return_value = (
            return_value.copy()
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )

        return res.success(return_value)

    ###################################
    # RETURN
    ###################################

    def visit_ReturnNode(self, node, context):
        res = RTResult()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))

            if res.should_return():
                return res

        else:
            value = Number.null

        return res.success_return(value)

    ###################################
    # CONTINUE
    ###################################

    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()

    ###################################
    # BREAK
    ###################################

    def visit_BreakNode(self, node, context):
        return RTResult().success_break()


#######################################
# TABLA GLOBAL
#######################################

global_symbol_table = SymbolTable()

global_symbol_table.set("NULL", Number.null)

global_symbol_table.set("FALSE", Number.false)

global_symbol_table.set("TRUE", Number.true)

global_symbol_table.set("MATH_PI", Number.math_PI)

global_symbol_table.set("PRINT", BuiltInFunction.print)

global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)

global_symbol_table.set("INPUT", BuiltInFunction.input)

global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)

global_symbol_table.set("CLEAR", BuiltInFunction.clear)

global_symbol_table.set("CLS", BuiltInFunction.clear)

global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)

global_symbol_table.set("IS_STR", BuiltInFunction.is_string)

global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)

global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)

global_symbol_table.set("TYPE", BuiltInFunction.type)

global_symbol_table.set("STR", BuiltInFunction.str)

global_symbol_table.set("NUM", BuiltInFunction.num)

global_symbol_table.set("APPEND", BuiltInFunction.append)

global_symbol_table.set("POP", BuiltInFunction.pop)

global_symbol_table.set("EXTEND", BuiltInFunction.extend)

global_symbol_table.set("LEN", BuiltInFunction.len)

global_symbol_table.set("RANGE", BuiltInFunction.range)

global_symbol_table.set("ABS", BuiltInFunction.abs)

global_symbol_table.set("MIN", BuiltInFunction.min)

global_symbol_table.set("MAX", BuiltInFunction.max)

global_symbol_table.set("SLEEP", BuiltInFunction.sleep)

global_symbol_table.set("ASSERT", BuiltInFunction.assert_)

global_symbol_table.set("RUN", BuiltInFunction.run)


#######################################
# RUN
#######################################


def run(fn, text):
    lexer = Lexer(fn, text)

    tokens, error = lexer.make_tokens()

    if error:
        return None, error

    parser = Parser(tokens)

    ast = parser.parse()

    if ast.error:
        return None, ast.error

    interpreter = Interpreter()

    context = Context("<program>")

    context.symbol_table = global_symbol_table

    result = interpreter.visit(ast.node, context)

    return result.value, result.error


#######################################
# SHELL
#######################################


def main():
    print("LoxBasic 2.0")
    print('Escribe "exit" para salir.')
    print()

    while True:
        try:
            text = input("LoxBasic > ")

        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.strip() == "":
            continue

        if text.strip().lower() == "exit":
            break

        result, error = run("<stdin>", text)

        if error:
            print(error.as_string())

        elif result is not None:
            if isinstance(result, List):
                if len(result.elements) == 1:
                    print(repr(result.elements[0]))
                elif len(result.elements) > 1:
                    print(repr(result))

            else:
                print(repr(result))


#######################################
# ENTRY POINT
#######################################

if __name__ == "__main__":
    main()
