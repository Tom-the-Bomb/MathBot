# MathBot
---

### How to run your own instance:
1. Install the `3.10` python interpreter assuming you have not done so already [here](https://www.python.org/downloads/release/python-3100/).
2. if you have git you can clone the repository with:
    ```bash
    $ git clone https://github.com/Tom-the-Bomb/Discord-Games.git
    ```
    - if you do not: install and configure git
    - alternatively you can install the `ZIP` of the repository [here](https://github.com/Tom-the-Bomb/Discord-Games/archive/refs/heads/master.zip).
3. Install the requrements with (in the repository directory):
```bash
$ py -m pip install -r requirements.txt
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
5. `cd` into the project directory and run the bot with `$ py launcher.py`