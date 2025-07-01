from datetime import date
from pathlib import Path

from anki_addons_dataset.argument.script_arguments import ScriptArguments
from anki_addons_dataset.facade.facade import Facade

if __name__ == "__main__":
    arguments: ScriptArguments = ScriptArguments()
    creation_date: date = arguments.get_creation_date()
    print(f"Creation date: {creation_date}")

    offline: bool = True
    working_dir: Path = Path.home() / "anki-addons-dataset"
    facade: Facade = Facade(working_dir)
    facade.create_datasets(offline)
