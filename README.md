
# MathBot

- A mathematics bot with specific algebraic functions and a calculator that is completely overkill for what it needs to be
- Made for a project in 9th grade mathematics

---

## How to run your own instance

1. Install a `>=3.10` python interpreter assuming you have not done so already [here](https://www.python.org/downloads/release/python-3100/).
2. if you have `git` installed you can clone the repository with:

    ```powershell
    PS > git clone https://github.com/Tom-the-Bomb/MathBot.git
    ```

    - __If you do not__: install and configure git
    - alternatively you can download the `ZIP` of the repository [here](https://github.com/Tom-the-Bomb/MathBot/archive/refs/heads/master.zip).
3. Install the requrements with (in the repository directory):

    ```powershell
    PS > py -m pip install -r requirements.txt
    ```

4. create a `config.json` file in the project directory and have this in it:

    ```json
    {
        "DEFAULT_PREFIXES": [
            "your bot prefix"
        ],
        "TOKEN": "your token here"
    }
    ```

5. `cd` into the project directory and run the bot using

    ```PS
    PS > py launcher.py
    ```
