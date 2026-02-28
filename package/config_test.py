import os
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import Literal
from typing import cast

from package.config import CONFIG_ENV_VAR
from package.config import Config
from package.config import load_config


class ChildConfig(Config):
    enabled: bool


class RootConfig(Config):
    name: str
    tags: list[str]
    limits: dict[str, int]
    coords: tuple[int, int]
    mode: Literal["debug", "prod"]
    child: ChildConfig


class IntOnlyConfig(Config):
    retries: int


class UnionValueConfig(Config):
    value: ChildConfig | str


class ConfigTests(unittest.TestCase):
    def test_from_mapping_success(self) -> None:
        cfg = RootConfig.from_mapping(
            {
                "name": "svc",
                "tags": ["a", "b"],
                "limits": {"cpu": 2},
                "coords": [1, 2],
                "mode": "debug",
                "child": {"enabled": True},
            }
        )
        self.assertEqual(cfg.name, "svc")
        self.assertEqual(cfg.coords, (1, 2))
        self.assertEqual(cfg.limits["cpu"], 2)
        self.assertTrue(cfg.child.enabled)

    def test_container_item_type_validation(self) -> None:
        with self.assertRaises(TypeError):
            RootConfig.from_mapping(
                {
                    "name": "svc",
                    "tags": ["a", 1],
                    "limits": {"cpu": 2},
                    "coords": [1, 2],
                    "mode": "debug",
                    "child": {"enabled": True},
                }
            )

        with self.assertRaises(TypeError):
            RootConfig.from_mapping(
                {
                    "name": "svc",
                    "tags": ["a"],
                    "limits": {"cpu": "2"},
                    "coords": [1, 2],
                    "mode": "debug",
                    "child": {"enabled": True},
                }
            )

    def test_tuple_length_validation(self) -> None:
        with self.assertRaises(TypeError):
            RootConfig.from_mapping(
                {
                    "name": "svc",
                    "tags": ["a"],
                    "limits": {"cpu": 2},
                    "coords": [1, 2, 3],
                    "mode": "debug",
                    "child": {"enabled": True},
                }
            )

    def test_reject_bool_for_int(self) -> None:
        with self.assertRaises(TypeError):
            IntOnlyConfig.from_mapping({"retries": True})

    def test_reject_non_string_mapping_key(self) -> None:
        payload = cast(
            Mapping[str, object],
            {
                1: "svc",
                "tags": ["a"],
                "limits": {"cpu": 2},
                "coords": [1, 2],
                "mode": "debug",
                "child": {"enabled": True},
            },
        )
        with self.assertRaises(TypeError):
            RootConfig.from_mapping(payload)

    def test_load_config_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                '[application]\nname = "svc"\nmode = "debug"\nsecret = "x"\n'
                '[application.time_zone]\nname = "Asia/Shanghai"\n'
                '[application.time_zone.fixed_zone]\nname = "CST"\noffset = 28800\n'
                "[application.logger]\nversion = 1\n",
                encoding="utf-8",
            )

            original_env = os.environ.get(CONFIG_ENV_VAR)
            os.environ[CONFIG_ENV_VAR] = str(config_path)
            try:
                loaded = load_config()
            finally:
                if original_env is None:
                    os.environ.pop(CONFIG_ENV_VAR, None)
                else:
                    os.environ[CONFIG_ENV_VAR] = original_env

            self.assertIn("application", loaded)

    def test_union_with_nested_config_and_scalar(self) -> None:
        nested_cfg = UnionValueConfig.from_mapping({"value": {"enabled": True}})
        self.assertTrue(cast(ChildConfig, nested_cfg.value).enabled)

        scalar_cfg = UnionValueConfig.from_mapping({"value": "raw-string"})
        self.assertEqual(cast(str, scalar_cfg.value), "raw-string")

    def test_reject_unknown_field(self) -> None:
        with self.assertRaises(ValueError):
            RootConfig.from_mapping(
                {
                    "name": "svc",
                    "tags": ["a", "b"],
                    "limits": {"cpu": 2},
                    "coords": [1, 2],
                    "mode": "debug",
                    "child": {"enabled": True},
                    "unk": "x",
                }
            )


if __name__ == "__main__":
    unittest.main()
