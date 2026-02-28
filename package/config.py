import dataclasses
import enum
import os
import sys
import tomllib
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from types import UnionType
from typing import Any
from typing import Final
from typing import Literal
from typing import TypeVar
from typing import Union
from typing import cast
from typing import dataclass_transform
from typing import get_args
from typing import get_origin
from typing import get_type_hints

from package.command import CommandContext
from package.command import CommandException
from package.command import CommandOption

CONFIG_ENV_VAR: Final = "CONFIG_FILE_PATH"
DEFAULT_CONFIG_FILE_PATH: Final = Path("config.toml")
_MISSING: Final = object()


def _type_error(config_key: str, expected_type: Any) -> TypeError:
    return TypeError(f"{config_key} must be set {expected_type}.")


def _normalize_path(path: Path) -> Path:
    normalized_path = path.expanduser().resolve()
    if normalized_path.suffix.lower() != ".toml":
        raise ValueError(f"Config file must be a TOML file (*.toml): {normalized_path}")
    if not normalized_path.exists():
        raise ValueError(f"Config file ({normalized_path}) does not exist.")
    if not normalized_path.is_file():
        raise ValueError(f"Config file ({normalized_path}) is not a file.")
    return normalized_path


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Config file is not valid TOML: {path}") from exc


def normalize_config_file_path(_: CommandContext, __: CommandOption, value: Path | None) -> Path | None:
    if value is None:
        return None

    try:
        normalized_path = _normalize_path(value)
        _load_toml(normalized_path)
        return normalized_path
    except ValueError as exc:
        raise CommandException(str(exc)) from exc


def get_config_file_path() -> Path | None:
    env_path = os.getenv(CONFIG_ENV_VAR)
    if not env_path:
        return None
    return _normalize_path(Path(env_path))


def load_config(config_file_path: Path | None = None) -> dict[str, Any]:
    resolved_path = _normalize_path(config_file_path) if config_file_path is not None else get_config_file_path()
    if resolved_path is None:
        raise ValueError(f"The config file is not specified. Use --config/-c or {CONFIG_ENV_VAR}.")
    return _load_toml(resolved_path)


def _is_union_annotation(origin_type: Any) -> bool:
    return origin_type in {Union, UnionType}


def _coerce_literal(value: Any, annotation: Any, config_key: str) -> Any:
    allowed_values = get_args(annotation)
    if value not in allowed_values:
        raise _type_error(config_key, annotation)
    return value


def _coerce_enum(value: Any, annotation: type[enum.Enum], config_key: str) -> enum.Enum:
    try:
        return annotation(value=value)
    except ValueError as exc:
        allowed_values = [item.value for item in annotation]
        raise ValueError(f"Invalid value '{value}' for {config_key}. Valid values are {allowed_values}") from exc


def _coerce_union(value: Any, annotation: Any, config_key: str) -> Any:
    for arg in get_args(annotation):
        if arg is type(None) and value is None:
            return None
        try:
            return _coerce_value(value=value, annotation=arg, config_key=config_key)
        except (TypeError, ValueError):
            continue
    raise _type_error(config_key, annotation)


def _coerce_list(value: Any, annotation: Any, config_key: str) -> list[Any]:
    if not isinstance(value, list):
        raise _type_error(config_key, annotation)
    typed_value = cast(list[Any], value)
    item_args = get_args(annotation)
    if len(item_args) != 1:
        return typed_value

    item_annotation = item_args[0]
    return [_coerce_value(item, item_annotation, f"{config_key}[{idx}]") for idx, item in enumerate(typed_value)]


def _coerce_dict(value: Any, annotation: Any, config_key: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _type_error(config_key, annotation)
    typed_value = cast(dict[Any, Any], value)
    item_args = get_args(annotation)
    if len(item_args) != 2:
        return cast(dict[str, Any], typed_value)

    key_annotation, value_annotation = item_args
    coerced: dict[Any, Any] = {}
    for key, item in typed_value.items():
        coerced_key = _coerce_value(key, key_annotation, f"{config_key}.<key>")
        coerced_value = _coerce_value(item, value_annotation, f"{config_key}[{key!r}]")
        coerced[coerced_key] = coerced_value
    return cast(dict[str, Any], coerced)


def _coerce_tuple(value: Any, annotation: Any, config_key: str) -> tuple[Any, ...]:
    if isinstance(value, list):
        list_value = cast(list[Any], value)
        value = tuple(list_value)
    if not isinstance(value, tuple):
        raise _type_error(config_key, annotation)
    typed_value = cast(tuple[Any, ...], value)

    item_args = get_args(annotation)
    if not item_args:
        return typed_value

    if len(item_args) == 2 and item_args[1] is Ellipsis:
        item_annotation = item_args[0]
        return tuple(_coerce_value(item, item_annotation, f"{config_key}[{idx}]") for idx, item in enumerate(typed_value))

    if len(typed_value) != len(item_args):
        raise _type_error(config_key, annotation)

    item_annotations = cast(tuple[Any, ...], item_args)
    return tuple(
        _coerce_value(item, item_annotation, f"{config_key}[{idx}]")
        for idx, (item, item_annotation) in enumerate(zip(typed_value, item_annotations, strict=True))
    )


def _coerce_value(value: Any, annotation: Any, config_key: str) -> Any:
    if annotation is Any:
        return value

    if isinstance(annotation, type) and issubclass(annotation, Config):
        if not isinstance(value, Mapping):
            raise _type_error(config_key, annotation)
        return annotation.from_mapping(config_data=cast(Mapping[str, Any], value), parent_key=config_key)

    origin_type = get_origin(annotation)

    if origin_type is Literal:
        return _coerce_literal(value=value, annotation=annotation, config_key=config_key)

    if _is_union_annotation(origin_type):
        return _coerce_union(value=value, annotation=annotation, config_key=config_key)

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return _coerce_enum(value=value, annotation=annotation, config_key=config_key)

    if annotation is int and isinstance(value, bool):
        raise _type_error(config_key, annotation)

    if origin_type is list:
        return _coerce_list(value=value, annotation=annotation, config_key=config_key)

    if origin_type is dict:
        return _coerce_dict(value=value, annotation=annotation, config_key=config_key)

    if origin_type is tuple:
        return _coerce_tuple(value=value, annotation=annotation, config_key=config_key)

    try:
        if not isinstance(value, annotation):
            raise _type_error(config_key, annotation)
    except TypeError as exc:
        raise _type_error(config_key, annotation) from exc

    return value


def _default_value(field: dataclasses.Field[Any], config_key: str) -> Any:
    if field.default is not dataclasses.MISSING:
        return field.default
    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()
    raise ValueError(f"{config_key} must be set.")


C = TypeVar("C", bound="Config")


@dataclass_transform(kw_only_default=True, field_specifiers=(dataclasses.field,))
class ConfigMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> Any:
        new_cls = super().__new__(cls, name, bases, namespace)
        return dataclasses.dataclass(frozen=True, kw_only=True)(new_cls)


class Config(metaclass=ConfigMeta):
    @staticmethod
    @lru_cache(maxsize=None)
    def _cached_type_hints(config_cls: type["Config"]) -> dict[str, Any]:
        return get_type_hints(
            config_cls,
            globalns=vars(sys.modules[config_cls.__module__]),
            localns=dict(vars(config_cls)),
            include_extras=True,
        )

    @classmethod
    def from_mapping(cls: type[C], config_data: Mapping[str, Any], parent_key: str = "") -> C:
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"config class({cls.__qualname__}) is not a dataclass")

        for key in cast(Mapping[Any, Any], config_data):
            if not isinstance(key, str):
                raise TypeError(f"{parent_key or '<root>'} contains non-string key: {key!r}")

        field_names = {field.name for field in dataclasses.fields(cls)}
        unknown_fields = [key for key in config_data if key not in field_names]
        if unknown_fields:
            unknown_fields_str = ", ".join(sorted(unknown_fields))
            raise ValueError(f"{parent_key or '<root>'} contains unknown fields: {unknown_fields_str}")

        values: dict[str, Any] = {}
        type_hints = cls._cached_type_hints(cls)

        for field in dataclasses.fields(cls):
            config_key = f"{parent_key}{parent_key and '.'}{field.name}"
            annotation = type_hints.get(field.name, Any)
            raw_value = config_data.get(field.name, _MISSING)

            if raw_value is _MISSING:
                values[field.name] = _default_value(field=field, config_key=config_key)
                continue

            values[field.name] = _coerce_value(value=raw_value, annotation=annotation, config_key=config_key)

        return cls(**values)

    @classmethod
    def load(cls: type[C], config_file_path: Path | None = None) -> C:
        return cls.from_mapping(config_data=load_config(config_file_path=config_file_path))
