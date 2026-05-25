from __future__ import annotations

from collections.abc import Iterable

from app.agent.tools.schemas import ToolManifest, ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.name in self._tools:
            raise ValueError(f"tool {spec.name} is already registered")
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"tool {name} is not registered") from exc

    def get_manifest(self, name: str) -> ToolManifest:
        return self.get(name).manifest()

    def list_manifests(self) -> list[ToolManifest]:
        return [spec.manifest() for spec in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    def register_many(self, specs: Iterable[ToolSpec]) -> None:
        for spec in specs:
            self.register(spec)
