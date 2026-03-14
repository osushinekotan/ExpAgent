"""src.kaggle_ops.new のテスト。"""

import shutil
from pathlib import Path

import pytest

from src.kaggle_ops.new import _post_process, exp


@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    """テンプレートディレクトリを tmp_path に再現する。"""
    src = Path("templates/models")
    dest = tmp_path / "templates" / "models"
    shutil.copytree(src, dest)
    return dest


@pytest.fixture
def models_dir(tmp_path: Path) -> Path:
    d = tmp_path / "models"
    d.mkdir()
    return d


class TestPostProcess:
    """_post_process のテスト。"""

    def test_template_replaces_placeholder(self, tmp_path: Path) -> None:
        """テンプレートから作成時、__EXP_NAME__ が置換される。"""
        target = tmp_path / "exp001"
        target.mkdir()
        (target / "README.md").write_text("---\nname: __EXP_NAME__\nbase_experiment: null\n---\n")
        (target / "train.py").write_text('settings = DirectorySettings(exp_name="template")\n')

        _post_process(target, "exp001", "template")

        readme = (target / "README.md").read_text()
        assert "name: exp001" in readme
        assert "__EXP_NAME__" not in readme
        assert "base_experiment: null" in readme

        train = (target / "train.py").read_text()
        assert 'exp_name="exp001"' in train
        assert 'exp_name="template"' not in train

    def test_source_sets_base_experiment(self, tmp_path: Path) -> None:
        """既存実験からコピー時、base_experiment がソース名に設定される。"""
        target = tmp_path / "exp002"
        target.mkdir()
        (target / "README.md").write_text("---\nname: exp001\nbase_experiment: null\n---\n")
        (target / "train.py").write_text('settings = DirectorySettings(exp_name="exp001")\n')

        _post_process(target, "exp002", "exp001")

        readme = (target / "README.md").read_text()
        assert "name: exp002" in readme
        assert "name: exp001" not in readme
        assert "base_experiment: exp001" in readme

        train = (target / "train.py").read_text()
        assert 'exp_name="exp002"' in train

    def test_missing_readme_no_error(self, tmp_path: Path) -> None:
        """README.md がなくてもエラーにならない。"""
        target = tmp_path / "exp001"
        target.mkdir()
        _post_process(target, "exp001", "template")

    def test_missing_train_py_no_error(self, tmp_path: Path) -> None:
        """train.py がなくてもエラーにならない。"""
        target = tmp_path / "exp001"
        target.mkdir()
        (target / "README.md").write_text("---\nname: __EXP_NAME__\n---\n")
        _post_process(target, "exp001", "template")


class TestExp:
    """exp コマンドのテスト。"""

    def test_create_from_template(self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """テンプレートから実験を作成できる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        exp("exp001", source="template")

        target = models_dir / "exp001"
        assert target.exists()
        assert (target / "README.md").exists()
        assert (target / "train.py").exists()

        readme = (target / "README.md").read_text()
        assert "name: exp001" in readme
        assert "base_experiment: null" in readme

        train = (target / "train.py").read_text()
        assert 'exp_name="exp001"' in train

    def test_create_from_existing(self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """既存実験からコピーして作成できる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        # まず exp001 を作成
        exp("exp001", source="template")
        # exp001 から exp002 を作成
        exp("exp002", source="exp001")

        target = models_dir / "exp002"
        readme = (target / "README.md").read_text()
        assert "name: exp002" in readme
        assert "base_experiment: exp001" in readme

        train = (target / "train.py").read_text()
        assert 'exp_name="exp002"' in train

    def test_already_exists_raises(self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG002
        """既に存在するディレクトリには作成できない。"""
        monkeypatch.chdir(template_dir.parent.parent)
        exp("exp001", source="template")

        with pytest.raises(AssertionError, match="Already exists"):
            exp("exp001", source="template")

    def test_source_not_found_raises(self, template_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """存在しないソースを指定するとエラーになる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        with pytest.raises(AssertionError, match="Source not found"):
            exp("exp001", source="nonexistent")
