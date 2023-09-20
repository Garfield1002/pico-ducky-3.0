'''
Interpreter for pico-ducky-3.0 scripts

These scripts need to be compiled using a compiler of the same version into a inject.bin file.

The main bottleneck in CircuitPython I ran into is the call stack size,
this code is optimized to remove as many function calls as possible.

License : GPLv2.0
Author: Jack ROYER (Garfield1002)
(c) 2023  Jack ROYER
'''
import board
import digitalio
import time
import random
import binascii
import zlib
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

# ================================
# CONSTANTS
# ================================

# Version of this script
VERSION = "0.5.dev"

# Name of the script to load
FILE_NAME = "inject.bin"

# Get logs on serial terminal
DEBUG = False

# Max int size in ducky script, values are stored mod max int
MAX_INT = 2 ** 16 - 1

# Character sets
LOWERCASE_LETTER = "abcdefghijklmnopqrstuvwxyz"
UPPERCASE_LETTER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBER = "0123456789"
SPECIAL = "!@#$%^&*()"
LETTER = LOWERCASE_LETTER + UPPERCASE_LETTER
CHARACTER = LETTER + NUMBER + SPECIAL


# Setup the LED pin.
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

supported_keyboards = {
    "en-US": KeyboardLayoutUS,
}


def log(msg: str):
    """
    Logs the message to the console
    """
    if DEBUG:
        print(f'[*] {time.time()}: {msg}')


class Interpreter:
    """
    Interpreter
    """


    def __init__(self, program, lang="en-US"):
        # List of instructions
        self.program: list[str] = program

        # Dictionary containing variable names and their values
        self.variables: dict[str, int]

        # Index of the current instruction (Instruction Pointer)
        self.ip: int

        # Stack of return addresses
        self.return_addresses: list[int]

        # Calculation stack
        self.calc_stack: list[int]

        # Keyboard and layout objects
        self.kbd = Keyboard(usb_hid.devices)
        self.layout = supported_keyboards[lang](self.kbd)

        # Saved lock key values
        self.saved_num: int
        self.saved_caps: int
        self.saved_scroll: int

        # Initializes properties
        self.init()

    def init(self):
        '''
        Sets all variable to their initial values
        '''
        self.variables = {
            "$_RANDOM_MIN": 1,
            "$_RANDOM_MAX": 9,
            "$_JITTER_MAX": 20,
            "$_JITTER_ENABLED": 0,
            "$_LED_SHOW_CAPS": 0,
            "$_LED_SHOW_NUM": 0,
            "$_LED_SHOW_SCROLL": 0,
        }
        self.ip = 0
        self.return_addresses = []
        self.calc_stack = []
        self.saved_num = 0
        self.saved_caps = 0
        self.saved_scroll = 0

        # TODO: This is kind of useless
        self.button_enabled = True

    def int_to_bool(self, i: int):
        '''
        Converts ints to bools before boolean operations
        '''
        if i != 0:
            return 1
        return 0

    def bool_to_int(self, b: bool):
        '''
        Converts bools to ints after boolean operations
        '''
        if b:
            return 1
        return 0

    def run(self):
        log(f"Starting the program")

        while True:
            # Retrieves next instruction
            t = self.program[self.ip]

            if DEBUG:
                time.sleep(0.05)
                log((t, self.calc_stack, self.return_addresses))

            # Execute next instruction
            if t == "NOOP":
                pass
            elif t == "":
                pass
            elif t == "STOP_PAYLOAD":
                return
            elif t == "RESTART_PAYLOAD":
                self.init()
                continue
            elif t == "SAVE_HOST_KEYBOARD_LOCK_STATE":
                self.saved_num = self.kbd.led_on(Keyboard.LED_NUM_LOCK)
                self.saved_caps = self.kbd.led_on(Keyboard.LED_CAPS_LOCK)
                self.saved_scroll = self.kbd.led_on(Keyboard.LED_SCROLL_LOCK)
            elif t == "RESTORE_HOST_KEYBOARD_LOCK_STATE":
                if (self.saved_num == 1) != self.kbd.led_on(Keyboard.LED_NUM_LOCK):
                    self.kbd.press(Keycode.NUM_LOCK)
                    time.sleep(.05)
                    self.kbd.release(Keycode.NUM_LOCK)
                if (self.saved_caps == 1) != self.kbd.led_on(Keyboard.LED_CAPS_LOCK):
                    self.kbd.press(Keycode.CAPS_LOCK)
                    time.sleep(.05)
                    self.kbd.release(Keycode.CAPS_LOCK)
                if (self.saved_scroll == 1) != self.kbd.led_on(Keyboard.LED_SCROLL_LOCK):
                    self.kbd.press(Keycode.SCROLL_LOCK)
                    time.sleep(.05)
                    self.kbd.release(Keycode.SCROLL_LOCK)
            elif t == "WAIT_FOR_CAPS_CHANGE":
                curr = self.kbd.led_on(Keyboard.LED_CAPS_LOCK)
                while 1:
                    if curr != self.kbd.led_on(Keyboard.LED_CAPS_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_CAPS_ON":
                while 1:
                    if 1 == self.kbd.led_on(Keyboard.LED_CAPS_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_CAPS_ON":
                while 1:
                    if 0 == self.kbd.led_on(Keyboard.LED_CAPS_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_NUM_CHANGE":
                curr = self.kbd.led_on(Keyboard.LED_NUM_LOCK)
                while 1:
                    if curr != self.kbd.led_on(Keyboard.LED_NUM_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_NUM_CHANGE_ON":
                while 1:
                    if 1 == self.kbd.led_on(Keyboard.LED_NUM_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_NUM_CHANGE_OFF":
                while 1:
                    if 0 == self.kbd.led_on(Keyboard.LED_NUM_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_SCROLL_CHANGE":
                curr = self.kbd.led_on(Keyboard.LED_SCROLL_LOCK)
                while 1:
                    if curr != self.kbd.led_on(Keyboard.LED_SCROLL_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_SCROLL_ON":
                while 1:
                    if 1 == self.kbd.led_on(Keyboard.LED_SCROLL_LOCK):
                        break
                    time.sleep(0.1)
            elif t == "WAIT_FOR_SCROLL_OFF":
                while 1:
                    if 0 == self.kbd.led_on(Keyboard.LED_SCROLL_LOCK):
                        break
                    time.sleep(0.1)
            elif t.startswith("STRING"):
                string = t.split(" ")[1]
                string = binascii.a2b_base64(string).decode("ascii")
                self.write_string(string)
            elif t.startswith("KEYS"):
                keys = t.split(" ")[1:]
                self.press_keys(keys)
            elif t == "LED_OFF":
                led.value = False
            elif t == "LED_G":
                led.value = True
            elif t == "LED_R":
                led.value = True
            elif t.startswith("JUMP"):
                self.ip = int(t.split(" ")[1])
                continue
            elif t.startswith("CALL"):
                self.return_addresses.append(self.ip + 1)
                self.ip = int(t.split(" ")[1])
                continue
            elif t == "RET":
                self.ip = self.return_addresses.pop()
                continue
            elif t.startswith("JZ"):
                condition = self.calc_stack.pop() == 0
                if condition:
                    self.ip = int(t.split(" ")[1])
                    continue
            elif t == "DELAY":
                val = self.calc_stack.pop()
                time.sleep(val / 1000)
            elif t == "RANDOM_LOWERCASE_LETTER":
                self.write_string(random.choice(LOWERCASE_LETTER.split("")))
            elif t == "RANDOM_UPPERCASE_LETTER":
                self.write_string(random.choice(UPPERCASE_LETTER.split("")))
            elif t == "RANDOM_LETTER":
                self.write_string(random.choice(LETTER.split("")))
            elif t == "RANDOM_NUMBER":
                self.write_string(random.choice(NUMBER.split("")))
            elif t == "RANDOM_SPECIAL":
                self.write_string(random.choice(SPECIAL.split("")))
            elif t == "RANDOM_CHAR":
                self.write_string(random.choice(CHARACTER.split("")))
            elif t == "DISABLE_BUTTON":
                self.button_enabled = False
            elif t == "ENABLE_BUTTON":
                self.button_enabled = True
            elif t.startswith("ASSIGNMENT"):
                var = t.split(" ")[1]
                val = self.calc_stack.pop()
                self.variables[var] = val
            elif t.startswith("PUSHI"):
                val = int(t.split(" ")[1]) % MAX_INT
                self.calc_stack.append(val)
            elif t == "POP":
                self.calc_stack.pop()
            elif t.startswith("PUSH"):
                var = t.split(" ")[1]
                val = 0

                if var == "$_RANDOM_INT":
                    val = random.randint(
                        self.variables["$_RANDOM_MIN"], self.variables["$_RANDOM_MAX"]
                    )
                elif var == "$_RANDOM_LOWER_LETTER_KEYCODE":
                    val = ord(random.choice(LOWERCASE_LETTER.split('')))
                elif var == "$_RANDOM_UPPER_LETTER_KEYCODE":
                    val = ord(random.choice(UPPERCASE_LETTER.split('')))
                elif var == "$_RANDOM_LETTER_KEYCODE":
                    val = ord(random.choice(LETTER.split('')))
                elif var == "$_RANDOM_NUMBER_KEYCODE":
                    val = ord(random.choice(NUMBER.split('')))
                elif var == "$_RANDOM_SPECIAL_KEYCODE":
                    val = ord(random.choice(SPECIAL.split('')))
                elif var == "$_RANDOM_CHAR_KEYCODE":
                    val = ord(random.choice(CHARACTER.split('')))
                elif var == "$_SAVED_CAPSLOCK_ON":
                    val = self.saved_caps
                elif var == "$_SAVED_NUMLOCK_ON":
                    val = self.saved_num
                elif var == "$_SAVED_SCROLLLOCK_ON":
                    val = self.saved_scroll
                elif var == "$_CAPSLOCK_ON":
                    if self.kbd.led_on(Keyboard.LED_CAPS_LOCK):
                        val = 1
                    else:
                        val = 0
                elif var == "$_NUMLOCK_ON":
                    if self.kbd.led_on(Keyboard.LED_NUM_LOCK):
                        val = 1
                    else:
                        val = 0
                elif var == "$_SCROLL_ON":
                    if self.kbd.led_on(Keyboard.LED_SCROLL_LOCK):
                        val = 1
                    else:
                        val = 0
                else:
                    val = self.variables[var]
                self.calc_stack.append(val)
            elif t.startswith("BINOP"):
                operator = t.split(" ")[1]
                right = self.calc_stack.pop()
                left = self.calc_stack.pop()
                val = 0

                if operator == "||":
                    val = self.bool_to_int(
                        self.int_to_bool(left) or self.int_to_bool(right)
                    )
                elif operator == "&&":
                    val = self.bool_to_int(
                        self.int_to_bool(left) and self.int_to_bool(right)
                    )
                elif operator == "==":
                    val = self.bool_to_int(left == right)
                elif operator == "!=":
                    val = self.bool_to_int(left != right)
                elif operator == "<=":
                    val = self.bool_to_int(left <= right)
                elif operator == ">=":
                    val = self.bool_to_int(left >= right)
                elif operator == "<":
                    val = self.bool_to_int(left < right)
                elif operator == ">":
                    val = self.bool_to_int(left > right)
                elif operator == "&":
                    val = (left & right) % MAX_INT
                elif operator == "|":
                    val = (left | right) % MAX_INT
                elif operator == "<<":
                    val = (left << right) % MAX_INT
                elif operator == ">>":
                    val = (left >> right) % MAX_INT
                elif operator == "+":
                    val = (left + right) % MAX_INT
                elif operator == "-":
                    val = (left - right) % MAX_INT
                elif operator == "*":
                    val = (left * right) % MAX_INT
                elif operator == "/":
                    val = (left // right) % MAX_INT
                elif operator == "%":
                    val = (left % right) % MAX_INT
                elif operator == "^":
                    val = (left ^ right) % MAX_INT
                else:
                    log(f"Unknown operator {operator}")
                self.calc_stack.append(val)
            else:
                log(f"Unknown instruction {t}")
                raise Exception()

            # Increment instruction pointer
            self.ip += 1

            # Exit the program if we reached EOF
            if self.ip >= len(self.program):
                break

        log("Program ended")

    def write_string(self, msg: str):
        if (self.variables["$_JITTER_ENABLED"]):
            for letter in msg:
                self.layout.write(letter)
                time.sleep(random.random() * (self.variables["$_JITTER_MAX"]) / 1000)
        else:
            self.layout.write(msg)

    def press_keys(self, keys: list[str]):
        '''
        Press a chord of keys then releases all of them,
        Some keys need to be renamed

        TODO: the renaming might happen in the compiler in the future
        '''
        added_prefix_keys = [
            getattr(Keycode, _key.upper().replace("CAPSLOCK", "CAPS_LOCK"))
            for _key in keys
        ]
        self.kbd.press(*added_prefix_keys)
        time.sleep(0.05)
        self.kbd.release_all()


if __name__ == "__main__":
    try:
        log("Opening file")
        with open(FILE_NAME, "rb") as f:
            program = f.read()
        program = zlib.decompress(program).decode("ascii")
        program = program.split("\n")

        log("Interpreting")
        interpreter = Interpreter(program)
        interpreter.run()

    except Exception as e:
        log(" ====================== ERROR ====================== ")
        log(e)
