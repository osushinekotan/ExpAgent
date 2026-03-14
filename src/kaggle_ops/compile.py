import logging
import tempfile
from pathlib import Path

import dotenv
import tyro
from stickytape import script

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


def compile_train_script(exp: str) -> str:
    exp_dir = Path(f"models/{exp}")
    train_path = exp_dir / "train.py"

    if not train_path.exists():
        raise FileNotFoundError(train_path)

    compiled = script(str(train_path), add_python_paths=[str(exp_dir)])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, prefix=f"compiled_{exp}_") as tmp:
        tmp.write(compiled)
    print(f"Compiled: {tmp.name}")
    return tmp.name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    tyro.cli(compile_train_script)
