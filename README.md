# 🦆 pico-ducky-3.0 🦆

> This project was heavily inspired by dbisu's [pico-ducky](https://github.com/dbisu/pico-ducky) but expands on it by adding limited support for DuckyScript 3.0

This project contains a **compiler** that you need on your computer to compile your scripts to an `inject.bin` and an **interpreter** that goes on your Pico and runs the code in the `inject.bin`.

## ⚡ Quick start

This installation guide assumes you have a Pico running [CircuitPython](https://circuitpython.org/).

Copy `interpreter/code.py` and `interpreter/boot.py` to the root of your Pico.

You need to install `simple_chalk` for the compiler.

## 💿 Compilation

To compile a script, run

```
$ python3 ./compiler/ducky3.py ./example.ducky
```

You can then copy the `inject.bin` compilation output to the root of your Pico.

## ✅ Limitations and required work

This is a very new project and does not fully support DuckyScript 3.0 yet

### Not supported yet

- Anything linked to storage on the Pico:
  - `HIDE_PAYLOAD`
  - `RESTORE_PAYLOAD`
  - `EXFIL`
  - `$_RANDOM_SEED`
- `ATTACKMODE` is not supported
  - `$_CURRENT_VID`
  - `$_CURRENT_PID`
  - `$_CURRENT_ATTACKMODE`
- Anything with the button is not supported:
  - `WAIT_FOR_BUTTON_PRESS`
  - `BUTTON_DEF`
  - `DISABLE_BUTTON`
  - `ENABLE_BUTTON`
  - `SAVE_ATTACKMODE`
  - `RESTORE_ATTACKMODE`
  - `$_BUTTON_ENABLED`
  - `$_BUTTON_USER_DEFINED`
  - `$_BUTTON_PUSH_RECEIVED`
  - `$_BUTTON_TIMEOUT`
- The key press currently releases all the keys, I'm not sure how to make these work with that
  - `HOLD`
  - `RELEASE`
  - `RESET`
- I'm not too sure what these do
  - `$_HOST_CONFIGURATION_REQUEST_COUNT`
  - `$_EXFIL_MODE_ENABLED`
  - `$_STORAGE_ACTIVITY_TIMEOUT`
  - `$_RECEIVED_HOST_LOCK_LED_REPLY`
- OS detection
  - `$_OS`

## License

This code is licensed under the GPLv3 license. Check out `license.md` for additional details.

## Contribution

This is a new project, bugs are expected and contributions are welcome
