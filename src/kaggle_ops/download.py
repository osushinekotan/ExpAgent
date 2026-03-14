import logging
import os

import dotenv
from kaggle import KaggleApi
from tyro.extras import SubcommandApp

from .utils.customhub import competition_download, datasets_download

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()
app = SubcommandApp()
logger = logging.getLogger(__name__)

COMP = os.getenv("COMPETITION_NAME", "")
INPUT_DIR = "./data/input"


@app.command()
def competition_dataset(force_download: bool = False) -> None:
    competition_download(client=client, handle=COMP, destination=INPUT_DIR, force_download=force_download)


@app.command()
def datasets(handles: list[str], force_download: bool = False) -> None:
    datasets_download(client=client, handles=handles, destination=INPUT_DIR, force_download=force_download)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    app.cli()
