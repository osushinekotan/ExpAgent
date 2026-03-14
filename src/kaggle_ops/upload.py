import logging
import os
from pathlib import Path

import dotenv
from kaggle import KaggleApi
from tyro.extras import SubcommandApp

from .utils.customhub import model_upload

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()
app = SubcommandApp()
logger = logging.getLogger(__name__)

USERNAME = os.getenv("KAGGLE_USERNAME", "")
COMP = os.getenv("COMPETITION_NAME", "")


@app.command()
def models(exp: str) -> None:
    model_upload(
        client=client,
        handle=f"{USERNAME}/{COMP}-models/other/{exp}",
        local_model_dir=str(Path(f"models/{exp}")),
        update=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    app.cli()
