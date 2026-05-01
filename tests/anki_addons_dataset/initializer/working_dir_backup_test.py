from pathlib import Path
from freezegun import freeze_time
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup

@freeze_time("2026-05-01 14:25:45")
def test_rename_existing_working_dir(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup):
    assert working_dir.get_path().exists()
    exp_working_dir: Path = working_dir.get_path().parent / f"{working_dir.get_path().name}.bak-20260501-142545"
    assert not exp_working_dir.exists()
    working_dir_backup.rename_existing_working_dir()
    assert not working_dir.get_path().exists()
    assert exp_working_dir.exists()
