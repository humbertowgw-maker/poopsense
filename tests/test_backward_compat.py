import json
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


class BackwardCompatibilityTests(unittest.TestCase):
    def test_old_analyses_are_migrated_to_dog_and_remain_queryable(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "legacy.sqlite3"
            config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
            config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
            config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
            command.upgrade(config, "0001_create_analyses")

            engine = sa.create_engine(f"sqlite:///{database}")
            with engine.begin() as connection:
                connection.execute(sa.text(
                    "INSERT INTO analyses (result, created_at) VALUES (:result, CURRENT_TIMESTAMP)"
                ), {"result": json.dumps({"urgency": "normal"})})

            command.upgrade(config, "head")
            with engine.connect() as connection:
                row = connection.execute(sa.text(
                    "SELECT pet_type, result FROM analyses"
                )).mappings().one()
            self.assertEqual(row["pet_type"], "dog")
            self.assertIn("normal", row["result"])


if __name__ == "__main__":
    unittest.main()
