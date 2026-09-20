from __future__ import annotations

import json
import ipaddress
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import Paths
from .profiles import ProfileStore, validate_name
from .storage import Settings, atomic_write, exclusive_lock, initialize

CLIENTS = ("codex", "claude")
MODES = ("inherit", "profile", "off")


def validate_client(client: str) -> str:
    if client not in CLIENTS:
        raise ValueError("client must be codex or claude")
    return client


def validate_bypass_rule(rule: str) -> str:
    value = rule.strip()
    if not value or len(value) > 253 or any(char.isspace() for char in value):
        raise ValueError("bypass rule must be one host or IP without whitespace")
    if "://" in value or any(char in value for char in "/?#@"):
        raise ValueError("bypass rule must not contain a URL, path, query or credentials")
    candidate = value.lstrip(".")
    if ":" in candidate:
        try:
            ipaddress.ip_address(candidate.strip("[]"))
        except ValueError as error:
            raise ValueError("bypass rule must not include a port") from error
    return value


@dataclass
class ClientPolicy:
    mode: str = "inherit"
    profile: str = ""
    bypass: list[str] = field(default_factory=list)

    def validate(self) -> "ClientPolicy":
        if self.mode not in MODES:
            raise ValueError("policy mode must be inherit, profile or off")
        if self.mode == "profile":
            validate_name(self.profile)
        elif self.profile:
            raise ValueError("profile is only valid in profile mode")
        self.bypass = list(dict.fromkeys(validate_bypass_rule(item) for item in self.bypass))
        return self


class ClientPolicyStore:
    """Versioned client policy. Codex's selected profile remains in config.toml."""

    def __init__(self, paths: Paths):
        self.paths = paths

    def _read(self) -> dict[str, ClientPolicy]:
        if not self.paths.clients.exists():
            return {client: ClientPolicy() for client in CLIENTS}
        payload = json.loads(self.paths.clients.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("clients"), dict):
            raise ValueError("unsupported clients policy file")
        result = {client: ClientPolicy() for client in CLIENTS}
        for client, value in payload["clients"].items():
            validate_client(client)
            if not isinstance(value, dict):
                raise ValueError(f"invalid policy for {client}")
            result[client] = ClientPolicy(**value).validate()
        return result

    def _write(self, policies: dict[str, ClientPolicy]) -> None:
        initialize(self.paths)
        payload = {"schema_version": 1, "clients": {
            client: asdict(policies[client].validate()) for client in CLIENTS
        }}
        atomic_write(self.paths.clients, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def get(self, client: str) -> ClientPolicy:
        validate_client(client)
        policy = self._read()[client]
        if client == "codex":
            active = Settings.load(self.paths.settings).active
            policy.mode = "off" if active == "off" else "profile"
            policy.profile = "" if active == "off" else active
        return policy.validate()

    def set(self, client: str, mode: str, profile: str = "") -> ClientPolicy:
        validate_client(client)
        if client == "codex" and mode == "inherit":
            raise ValueError("Codex persistent policy must be profile or off; use direct entry to inspect inheritance")
        policy = ClientPolicy(mode, profile).validate()
        if mode == "profile":
            ProfileStore(self.paths).get(profile)
        with exclusive_lock(self.paths.lock):
            policies = self._read()
            policy.bypass = policies[client].bypass
            previous_settings = self.paths.settings.read_text(encoding="utf-8") if self.paths.settings.exists() else None
            if client == "codex":
                settings = Settings.load(self.paths.settings)
                settings.active = profile if mode == "profile" else "off"
                atomic_write(self.paths.settings, settings.dump())
            policies[client] = policy
            try:
                self._write(policies)
            except Exception:
                if client == "codex":
                    if previous_settings is None:
                        self.paths.settings.unlink(missing_ok=True)
                    else:
                        atomic_write(self.paths.settings, previous_settings)
                raise
        return self.get(client)

    def add_bypass(self, client: str, rule: str) -> ClientPolicy:
        validate_client(client)
        clean = validate_bypass_rule(rule)
        with exclusive_lock(self.paths.lock):
            policies = self._read()
            if clean not in policies[client].bypass:
                policies[client].bypass.append(clean)
            self._write(policies)
        return self.get(client)

    def remove_bypass(self, client: str, rule: str) -> ClientPolicy:
        validate_client(client)
        clean = validate_bypass_rule(rule)
        with exclusive_lock(self.paths.lock):
            policies = self._read()
            if clean not in policies[client].bypass:
                raise FileNotFoundError(f"bypass rule not found: {clean}")
            policies[client].bypass.remove(clean)
            self._write(policies)
        return self.get(client)
