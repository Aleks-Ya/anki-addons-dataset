from datetime import date
from pathlib import Path

from anki_addons_dataset.argument.script_arguments import ScriptArguments, Operation
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.facade.facade import Facade

if __name__ == "__main__":
    arguments: ScriptArguments = ScriptArguments()
    operation: Operation = arguments.get_operation()
    creation_date: date = arguments.get_creation_date()
    print(f"Creation date: {creation_date}")

    working_dir: WorkingDir = WorkingDir(Path.home() / "anki-addons-dataset")
    facade: Facade = Facade(working_dir)
    facade.process(operation, creation_date)
