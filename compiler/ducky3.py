'''
Compiler for pico-ducky-3.0 scripts.

License : GPLv2.0
Author: Jack ROYER (Garfield1002)
(c) 2023  Jack ROYER
'''
import re
import sys
import os
import zlib
import base64
from ply import lex
from ply import yacc

from simple_chalk import chalk

source_filename = ""

source = ""


def syntax_error(line: int, token: str, idx: int):
    (line, col) = get_string_coords(source, idx)
    line_str = str(line)
    line_str_len = len(line_str)
    print(
        f"""File "{source_filename}", line {line} col {col}
{" " * line_str_len} {chalk.blue("|")}
{line_str} {chalk.blue("|")} {source.splitlines()[line - 1]}
{" " * line_str_len} {chalk.blue("|")}{" " * (col - 1) + chalk.red("^") * len(token)}\n{chalk.red("Syntax Error")}: invalid token'
"""
    )


def get_string_coords(s: str, index: int) -> tuple[int, int]:
    """Returns (line_number, col) of `index` in `s`."""
    if not len(s):
        return 1, 1
    sp = s[: index + 1].splitlines(keepends=True)
    return len(sp), len(sp[-1])


reserved = {
    # Keys
    "UP": "UP",
    "DOWN": "DOWN",
    "LEFT": "LEFT",
    "RIGHT": "RIGHT",
    "UPARROW": "UPARROW",
    "DOWNARROW": "DOWNARROW",
    "LEFTARROW": "LEFTARROW",
    "RIGHTARROW": "RIGHTARROW",
    "PAGEUP": "PAGEUP",
    "PAGEDOWN": "PAGEDOWN",
    "HOME": "HOME",
    "END": "END",
    "INSERT": "INSERT",
    "DELETE": "DELETE",
    "DEL": "DEL",
    "BACKSPACE": "BACKSPACE",
    "TAB": "TAB",
    "SPACE": "SPACE",
    "ENTER": "ENTER",
    "ESCAPE": "ESCAPE",
    "PAUSE": "PAUSE",
    "BREAK": "BREAK",
    "PRINTSCREEN": "PRINTSCREEN",
    "MENU": "MENU",
    "APP": "APP",
    "F1": "F1",
    "F2": "F2",
    "F3": "F3",
    "F4": "F4",
    "F5": "F5",
    "F6": "F6",
    "F7": "F7",
    "F8": "F8",
    "F9": "F9",
    "F10": "F10",
    "F11": "F11",
    "F12": "F12",
    "SHIFT": "SHIFT",
    "ALT": "ALT",
    "CONTROL": "CONTROL",
    "CTRL": "CTRL",
    "COMMAND": "COMMAND",
    "WINDOWS": "WINDOWS",
    "GUI": "GUI",
    "CAPSLOCK": "CAPSLOCK",
    "NUMLOCK": "NUMLOCK",
    "SCROLLLOCK": "SCROLLLOCK",
    # Commands
    "EXFIL": "EXFIL",
    "DELAY": "DELAY",
    # Button
    "WAIT_FOR_BUTTON_PRESS": "WAIT_FOR_BUTTON_PRESS",
    "BUTTON_DEF": "BUTTON_DEF",
    "END_BUTTON": "END_BUTTON",
    "DISABLE_BUTTON": "DISABLE_BUTTON",
    "ENABLE_BUTTON": "ENABLE_BUTTON",
    # LED
    "LED_OFF": "LED_OFF",
    "LED_R": "LED_R",
    "LED_G": "LED_G",
    # Attack mode
    "ATTACKMODE": "ATTACKMODE",
    "HID": "HID",
    "STORAGE": "STORAGE",
    "OFF": "OFF",
    "RESTORE_ATTACKMODE": "RESTORE_ATTACKMODE",
    "SAVE_ATTACKMODE": "SAVE_ATTACKMODE",
    # Var
    "VAR": "VAR",
    # Bool
    "TRUE": "TRUE",
    "FALSE": "FALSE",
    # Control flow
    "IF": "IF",
    "THEN": "THEN",
    "END_IF": "END_IF",
    "ELSE": "ELSE",
    "WHILE": "WHILE",
    "END_WHILE": "END_WHILE",
    "FUNCTION": "FUNCTION",
    "END_FUNCTION": "END_FUNCTION",
    "RETURN": "RETURN",
    # Random
    "RANDOM_LOWERCASE_LETTER": "RANDOM_LOWERCASE_LETTER",
    "RANDOM_UPPERCASE_LETTER": "RANDOM_UPPERCASE_LETTER",
    "RANDOM_LETTER": "RANDOM_LETTER",
    "RANDOM_NUMBER": "RANDOM_NUMBER",
    "RANDOM_SPECIAL": "RANDOM_SPECIAL",
    "RANDOM_CHAR": "RANDOM_CHAR",
    # Holding
    "HOLD": "HOLD",
    "RELEASE": "RELEASE",
    # Payload
    "RESTART_PAYLOAD": "RESTART_PAYLOAD",
    "STOP_PAYLOAD": "STOP_PAYLOAD",
    "RESET": "RESET",
    "HIDE_PAYLOAD": "HIDE_PAYLOAD",
    "RESTORE_PAYLOAD": "RESTORE_PAYLOAD",
    # Lock
    "WAIT_FOR_CAPS_ON": "WAIT_FOR_CAPS_ON",
    "WAIT_FOR_CAPS_OFF": "WAIT_FOR_CAPS_OFF",
    "WAIT_FOR_CAPS_CHANGE": "WAIT_FOR_CAPS_CHANGE",
    "WAIT_FOR_NUM_ON": "WAIT_FOR_NUM_ON",
    "WAIT_FOR_NUM_OFF": "WAIT_FOR_NUM_OFF",
    "WAIT_FOR_NUM_CHANGE": "WAIT_FOR_NUM_CHANGE",
    "WAIT_FOR_SCROLL_ON": "WAIT_FOR_SCROLL_ON",
    "WAIT_FOR_SCROLL_OFF": "WAIT_FOR_SCROLL_OFF",
    "WAIT_FOR_SCROLL_CHANGE": "WAIT_FOR_SCROLL_CHANGE",
    "SAVE_HOST_KEYBOARD_LOCK_STATE": "SAVE_HOST_KEYBOARD_LOCK_STATE",
    "RESTORE_HOST_KEYBOARD_LOCK_STATE": "RESTORE_HOST_KEYBOARD_LOCK_STATE",
}

tokens = [
    "NEWLINE",
    "NUMBER",
    "REM",
    "STRING",
    "STRINGLN",
    "ID",
    "VID",
    "PID",
    "MAN",
    "PROD",
    "SERIAL",
    "VARIABLE",
    "EQ",
    "NE",
    "LE",
    "GE",
    "AND",
    "OR",
    "RS",
    "LS",
] + list(reserved.values())

# Regular expression rules for simple tokens
literals = ["=", "+", "-", "*", "/", "%", "^", ">", "<", "(", ")", "&", "|"]

# Numbers
def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


# REM and REM_BLOCK
def t_REM(t):
    r"(REM_BLOCK$(.+?)END_REM$)|(REM\s(.+?)$)"
    return t


# STRING
def t_STRING(t):
    r"(STRING$(.+?)END_STRING$)|(STRING\s(.+?)$)"
    t.value = t.value.lstrip()
    if "END_STRING" in t.value:
        value = ""
        t.value = t.value[7:-10]
        for line in t.value.splitlines():
            value += line.strip()
        t.value = value
    else:
        t.value = t.value[7:].rstrip()
    return t


# STRINGLN
def t_STRINGLN(t):
    r"(STRINGLN$(.+?)END_STRINGLN$)|(STRINGLN\s(.+?)$)"
    t.value = t.value.lstrip()
    if "END_STRINGLN" in t.value:
        value = ""
        t.value = t.value[9:-12]
        for line in t.value.splitlines():
            value += line[1:] + "\n"
        t.value = value
    else:
        t.value = t.value[9:] + "\n"
    return t


# Attack mode
def t_VID(t):
    r"VID_[0-9a-fA-F]{4}"
    t.value = int(t.value[4:], base=16)
    return t


def t_PID(t):
    r"PID_[0-9a-fA-F]{4}"
    t.value = int(t.value[4:], base=16)
    return t


def t_MAN(t):
    r"MAN_[0-9a-zA-Z]{,32}"
    t.value = t.value[4:]
    return t


def t_PROD(t):
    r"PROD_[0-9a-zA-Z]{,32}"
    t.value = t.value[5:]
    return t


def t_SERIAL(t):
    r"SERIAL_[0-9]{,12}"
    t.value = int(t.value[7:])
    return t


# VARIABLE
t_VARIABLE = r"\$[A-Za-z0=9_]+"

# Operators
t_EQ = r"=="
t_NE = r"!="
t_LE = r"<="
t_GE = r">="

t_AND = r"&&"
t_OR = r"\|\|"

t_RS = ">>"
t_LS = "<<"


# RESERVED
def t_ID(t):
    r"[A-Za-z_]+"
    t.type = reserved.get(t.value, "ID")  # Check for reserved words
    return t


# Define a rule so we can track line numbers
def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    t.type = "NEWLINE"
    return t


# A string containing ignored characters (spaces and tabs)
t_ignore = " \t"

# Error handling rule
def t_error(t):
    syntax_error(t.lexer.lineno, t.value[0], t.lexer.lexpos)
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex(reflags=re.MULTILINE | re.DOTALL | re.VERBOSE)  # , debug=1)


# =============================================================================
# PARSER
# =============================================================================

MAX_INT = 2 ** 16 - 1

HID = 1
STORAGE = 2

label_count = 0

precedence = [
    ("left", "AND", "OR"),
    ("left", "NE", "EQ", "LE", "GE", "<", ">"),
    ("left", "&", "|", "LS", "RS"),
    ("left", "+", "-"),
    ("left", "*", "/", "%"),
    ("left", "^"),
]


def write_string(s: str):
    # TODO:
    print(chalk.cyan(s), end="")


def p_program_empty(p):
    "program : empty"
    p[0] = ""


def p_program_statements(p):
    "program : statements program"
    p[0] = p[1] + p[2]


def p_program_BUTTON_DEF(p):
    "program : BUTTON_DEF NEWLINE statements END_BUTTON NEWLINE program"
    # p[0] = [("BUTTON_DEF", p[3])] + p[6]
    p[0] = p[6]


# Function


def p_program_FUNCTION(p):
    "program : FUNCTION ID '(' ')' NEWLINE statements END_FUNCTION NEWLINE program"
    global label_count
    p[0] = (
        f"JUMP LABEL_{label_count + 1}\n"
        + f"LABEL LABEL_{p[2]}:"
        + p[6]
        + "PUSHI 0\n"
        + "RET\n"
        + f"LABEL LABEL_{label_count + 1}:"
        + p[9]
    )
    label_count += 1


# Statements


def p_statements_empty(p):
    "statements : empty"
    p[0] = ""


def p_statements_NEWLINE(p):
    "statements : NEWLINE statements"
    p[0] = p[2]


def p_statements(p):
    "statements : statement NEWLINE statements"
    # p[3] should be a statement list
    p[0] = p[1] + p[3]


def p_empty(p):
    "empty :"
    pass


def p_statement_expression(p):
    "statement : expression"
    p[0] = p[1] + "POP\n"


def p_statement_REM(p):
    "statement : REM"
    p[0] = "NOOP\n"


def p_statement_RETURN(p):
    "statement : RETURN expression"
    p[0] = p[2] + "RET\n"


def p_statement_VAR(p):
    "statement : VAR VARIABLE '=' expression"
    p[0] = p[4] + f"ASSIGNMENT {p[2]}\n"


def p_statement_assignment(p):
    "statement : VARIABLE '=' expression"
    p[0] = p[3] + f"ASSIGNMENT {p[1]}\n"


def p_statement_STRING(p):
    "statement : STRING"
    p[0] = "STRING " + base64.b64encode(p[1].encode("ascii")).decode("ascii") + "\n"


def p_statement_STRINGLN(p):
    "statement : STRINGLN"
    p[0] = "STRING " + base64.b64encode(p[1].encode("ascii")).decode("ascii") + "\n"


# DELAY


def p_statement_DELAY(p):
    "statement : DELAY expression"
    p[0] = p[2] + "DELAY\n"


# Attack mode TODO:


def p_statement_ATTACKMODE(p):
    "statement : ATTACKMODE attackmode"
    # TODO:
    p[0] = ("ATTACKMODE",)


def p_statement_ATTACKMODE_optional(p):
    "statement : ATTACKMODE attackmode VID PID MAN PROD SERIAL"
    # TODO:
    p[0] = ("ATTACKMODE",)


def p_statement_SAVE_ATTACKMODE(p):
    "statement : SAVE_ATTACKMODE"
    pass


def p_statement_RESTORE_ATTACKMODE(p):
    "statement : RESTORE_ATTACKMODE"
    pass


def p_attackmode_HID(p):
    "attackmode : HID"
    return HID


def p_attackmode_STORAGE(p):
    "attackmode : STORAGE"
    return STORAGE


def p_attackmode_HID_STORAGE(p):
    """attackmode : HID STORAGE
    | STORAGE HID"""
    return HID | STORAGE


def p_attackmode_OFF(p):
    "attackmode : OFF"
    return 0


# If


def p_statement_IF(p):
    "statement : IF expression THEN NEWLINE statements else END_IF"
    global label_count
    p[0] = (
        p[2]
        + f"JZ LABEL_{label_count + 1}\n"
        + p[5]
        + f"JUMP LABEL_{label_count + 2}\n"
        + f"LABEL LABEL_{label_count + 1}:"
        + p[6]
        + f"LABEL LABEL_{label_count + 2}:"
    )
    label_count += 2


def p_else_empty(p):
    "else : empty"
    p[0] = "NOOP\n"


def p_else_IF(p):
    "else : ELSE IF expression THEN NEWLINE statements else"
    global label_count
    p[0] = (
        p[3]
        + f"JZ LABEL_{label_count + 1}\n"
        + p[6]
        + f"JUMP LABEL_{label_count + 2}\n"
        + f"LABEL LABEL_{label_count + 1}:"
        + p[7]
        + f"LABEL LABEL_{label_count + 2}:"
    )
    label_count += 2


def p_else_ELSE(p):
    "else : ELSE NEWLINE statements"
    p[0] = p[3]


# While


def p_statement_WHILE(p):
    "statement : WHILE expression NEWLINE statements END_WHILE"
    global label_count
    p[0] = (
        f"LABEL LABEL_{label_count + 1}:"
        + p[2]
        + f"JZ LABEL_{label_count + 2}\n"
        + p[4]
        + f"JUMP LABEL_{label_count + 1}\n"
        + f"LABEL LABEL_{label_count + 2}:"
    )
    label_count += 2


# Holding


def p_statemtent_HOLD(p):
    "statement : HOLD key"
    p[0] = f"HOLD {p[2]}\n"


def p_statemtent_RELEASE(p):
    "statement : RELEASE key"
    p[0] = f"RELEASE {p[2]}\n"


def p_statemtent_keys(p):
    "statement : key keys"
    p[0] = f"KEYS {''.join([p[1]] + p[2])}\n"


# Payload & Wait


def p_statement_command(p):
    """statement : RESTART_PAYLOAD
    | STOP_PAYLOAD
    | RESET
    | HIDE_PAYLOAD
    | RESTORE_PAYLOAD
    | WAIT_FOR_CAPS_ON
    | WAIT_FOR_CAPS_OFF
    | WAIT_FOR_CAPS_CHANGE
    | WAIT_FOR_NUM_ON
    | WAIT_FOR_NUM_OFF
    | WAIT_FOR_NUM_CHANGE
    | WAIT_FOR_SCROLL_ON
    | WAIT_FOR_SCROLL_OFF
    | WAIT_FOR_SCROLL_CHANGE
    | SAVE_HOST_KEYBOARD_LOCK_STATE
    | RESTORE_HOST_KEYBOARD_LOCK_STATE
    | RANDOM_LOWERCASE_LETTER
    | RANDOM_UPPERCASE_LETTER
    | RANDOM_LETTER
    | RANDOM_SPECIAL
    | RANDOM_NUMBER
    | RANDOM_CHAR
    | LED_OFF
    | LED_R
    | LED_G
    | WAIT_FOR_BUTTON_PRESS
    | DISABLE_BUTTON
    | ENABLE_BUTTON
    """
    p[0] = p[1] + "\n"


# Exfil


def p_statement_exfil(p):
    "statement : EXFIL expression"
    p[0] = p[2] + "EXFIL\n"


# Key


def p_key_ID(p):
    "key : ID"

    if len(p[1]) != 1:
        print(p[1])
        raise "aaa"
    p[0] = p[1]


def p_key(p):
    """key : UP
    | DOWN
    | LEFT
    | RIGHT
    | UPARROW
    | DOWNARROW
    | LEFTARROW
    | RIGHTARROW
    | PAGEUP
    | PAGEDOWN
    | HOME
    | END
    | INSERT
    | DELETE
    | DEL
    | BACKSPACE
    | TAB
    | SPACE
    | ENTER
    | ESCAPE
    | PAUSE
    | BREAK
    | PRINTSCREEN
    | MENU
    | APP
    | F1
    | F2
    | F3
    | F4
    | F5
    | F6
    | F7
    | F8
    | F9
    | F10
    | F11
    | F12
    | SHIFT
    | ALT
    | CONTROL
    | CTRL
    | COMMAND
    | WINDOWS
    | GUI
    | CAPSLOCK
    | NUMLOCK
    | SCROLLLOCK"""
    p[0] = p[1]


def p_keys_empty(p):
    "keys : empty"
    p[0] = []


def p_keys(p):
    "keys : key keys"
    p[0] = [p[1]] + p[2]


# Expression

reg_count = 0


def p_expression_call(p):
    "expression : ID '(' ')'"
    p[0] = f"CALL LABEL_{p[1]}\n"


def p_expression_parenthesis(p):
    "expression : '(' expression ')'"
    p[0] = p[2]


def p_expression_true(p):
    "expression : TRUE"
    p[0] = f"PUSHI 1\n"


def p_expression_false(p):
    "expression : FALSE"
    p[0] = f"PUSHI 0\n"


def p_expression_variable(p):
    "expression : VARIABLE"
    p[0] = f"PUSH {p[1]}\n"


def p_expression_number(p):
    "expression : NUMBER"
    p[0] = f"PUSHI {p[1]}\n"


def p_expression_binary_operators(p):
    """expression : expression AND expression
    | expression OR expression
    | expression EQ expression
    | expression NE expression
    | expression LE expression
    | expression GE expression
    | expression '<' expression
    | expression '>' expression
    | expression '&' expression
    | expression '|' expression
    | expression LS expression
    | expression RS expression
    | expression '+' expression
    | expression '-' expression
    | expression '*' expression
    | expression '/' expression
    | expression '%' expression
    | expression '^' expression
    """
    p[0] = p[1] + p[3] + f"BINOP {p[2]}\n"


# Error rule for syntax errors
def p_error(p):
    if p:
        print(chalk.red("Syntax error at token"), p.type, p.lineno)
    else:
        print(chalk.red("Syntax error at EOF"))


# Build the parser
parser = yacc.yacc(optimize=1)


def pre_processor(program: str) -> str:
    # adds a new line to the end of the program
    program += "\n"

    # replaces constants
    defines = re.findall(
        r"^[\s\t]*DEFINE\s(\#?[a-zA-Z_]+)\s(.+?)$",
        program,
        flags=re.MULTILINE | re.DOTALL | re.VERBOSE,
    )

    for define in defines:
        name, value = define
        program = program.replace(name, value)

    program = re.sub(
        r"^([\s\t]*DEFINE.+?)$",
        "",
        program,
        flags=re.MULTILINE | re.DOTALL | re.VERBOSE,
    )

    return program


def remove_labels(program: str) -> str:
    labels = {}

    prog = []
    for nb, line in enumerate(program.split("\n")):
        while line.startswith("LABEL"):
            split = line.split(":")
            line = ":".join(split[1:])
            labels[split[0][6:]] = nb
        prog.append(line)

    ret = []

    for line in prog:
        if line.startswith("JZ"):
            line = f"JZ {labels[line[3:]]}"

        elif line.startswith("JUMP"):
            line = f"JUMP {labels[line[5:]]}"

        elif line.startswith("CALL"):
            line = f"CALL {labels[line[5:]]}"

        ret.append(line)

    return "\n".join(ret)


def usage():
    print(
        """Open Ducky compiler
Generates an AST for a Ducky language

Usage duckyc <file>
"""
    )


if __name__ == "__main__":
    if len(sys.argv) != 1:
        pass

    if not os.path.exists(sys.argv[1]):
        pass

    filepath = sys.argv[1]
    filename = os.path.basename(filepath)

    source_filename = filepath

    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()

    data = pre_processor(data)

    source = data

    prog = parser.parse(data)
    prog = remove_labels(prog)
    prog = zlib.compress(bytes(prog, encoding="utf-8"))

    with open("inject.bin", "wb") as f:
        f.write(prog)
