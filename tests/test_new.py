"""src.new のテスト。"""

import shutil
from pathlib import Path

import pytest

from src.new import _post_process, _resolve_code_sub, exp


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


class TestResolveCodeSub:
    """_resolve_code_sub のテスト。"""

    def test_true(self) -> None:
        assert _resolve_code_sub("true") is True

    def test_false(self) -> None:
        assert _resolve_code_sub("false") is False

    def test_auto_kaggle_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPETITION_PLATFORM", "kaggle")
        monkeypatch.setenv("IS_CODE_COMPETITION", "true")
        assert _resolve_code_sub("auto") is True

    def test_auto_kaggle_non_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPETITION_PLATFORM", "kaggle")
        monkeypatch.setenv("IS_CODE_COMPETITION", "false")
        assert _resolve_code_sub("auto") is False

    def test_auto_non_kaggle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPETITION_PLATFORM", "signate")
        monkeypatch.setenv("IS_CODE_COMPETITION", "true")
        assert _resolve_code_sub("auto") is False

    def test_auto_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("COMPETITION_PLATFORM", raising=False)
        monkeypatch.delenv("IS_CODE_COMPETITION", raising=False)
        assert _resolve_code_sub("auto") is False


class TestPostProcess:
    """_post_process のテスト。"""

    def test_template_replaces_exp_name(self, tmp_path: Path) -> None:
        """テンプレートから作成時、train.py の exp_name が置換される。"""
        target = tmp_path / "exp001"
        target.mkdir()
        (target / "train.py").write_text('settings = DirectorySettings(exp_name="template")\n')

        _post_process(target, "exp001", "template")

        train = (target / "train.py").read_text()
        assert 'exp_name="exp001"' in train
        assert 'exp_name="template"' not in train

    def test_source_replaces_exp_name(self, tmp_path: Path) -> None:
        """既存実験からコピー時、train.py の exp_name が置換される。"""
        target = tmp_path / "exp002"
        target.mkdir()
        (target / "train.py").write_text('settings = DirectorySettings(exp_name="exp001")\n')

        _post_process(target, "exp002", "exp001")

        train = (target / "train.py").read_text()
        assert 'exp_name="exp002"' in train

    def test_missing_train_py_no_error(self, tmp_path: Path) -> None:
        """train.py がなくてもエラーにならない。"""
        target = tmp_path / "exp001"
        target.mkdir()
        _post_process(target, "exp001", "template")


class TestExp:
    """exp コマンドのテスト。"""

    def test_create_from_template(self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """テンプレートから実験を作成できる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        exp("exp001", source="template", kaggle_code_sub="false")

        target = models_dir / "exp001"
        assert target.exists()
        assert (target / "train.py").exists()
        assert not (target / "submission").exists()

        train = (target / "train.py").read_text()
        assert 'exp_name="exp001"' in train

    def test_create_with_kaggle_code_sub(
        self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """kaggle_code_sub="true" の場合、submission ディレクトリが含まれる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        exp("exp001", source="template", kaggle_code_sub="true")

        target = models_dir / "exp001"
        assert target.exists()
        assert (target / "submission").exists()

    def test_auto_includes_submission_for_kaggle_code_comp(
        self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """auto + kaggle + code competition の場合、submission が含まれる。"""
        monkeypatch.chdir(template_dir.parent.parent)
        monkeypatch.setenv("COMPETITION_PLATFORM", "kaggle")
        monkeypatch.setenv("IS_CODE_COMPETITION", "true")

        exp("exp001", source="template", kaggle_code_sub="auto")

        target = models_dir / "exp001"
        assert (target / "submission").exists()

    def test_auto_excludes_submission_for_non_code_comp(
        self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """auto + 非 code competition の場合、submission が除外される。"""
        monkeypatch.chdir(template_dir.parent.parent)
        monkeypatch.setenv("COMPETITION_PLATFORM", "kaggle")
        monkeypatch.setenv("IS_CODE_COMPETITION", "false")

        exp("exp001", source="template", kaggle_code_sub="auto")

        target = models_dir / "exp001"
        assert not (target / "submission").exists()

    def test_create_from_existing(self, template_dir: Path, models_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """既存実験からコピーして作成できる。"""
        monkeypatch.chdir(template_dir.parent.parent)

        exp("exp001", source="template")
        exp("exp002", source="exp001")

        target = models_dir / "exp002"
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
