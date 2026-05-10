"""
Docker lifecycle management for ImmoCalcul batch runs.
Provides safe stop/remove/create/run utilities with logging.
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DockerRunResult:
    returncode: int
    stdout: str
    stderr: str


def _run_command(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    logging.info("[DOCKER] %s", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def container_exists(name: str) -> bool:
    result = _run_command([
        "docker", "ps", "-a",
        "--filter", f"name=^{name}$",
        "--format", "{{.Names}}",
    ])
    return name in (result.stdout or "").splitlines()


def is_container_running(name: str) -> bool:
    result = _run_command([
        "docker", "ps",
        "--filter", f"name=^{name}$",
        "--format", "{{.Names}}",
    ])
    return name in (result.stdout or "").splitlines()


def stop_container(name: str) -> None:
    if is_container_running(name):
        result = _run_command(["docker", "stop", name])
        if result.returncode != 0:
            logging.warning("[DOCKER] Stop failed for %s: %s", name, result.stderr)


def remove_container(name: str) -> None:
    if container_exists(name):
        result = _run_command(["docker", "rm", "-f", name])
        if result.returncode != 0:
            logging.warning("[DOCKER] Remove failed for %s: %s", name, result.stderr)


def run_container(
    *,
    name: str,
    image: str,
    command: List[str],
    volumes: Dict[str, str],
    env: Dict[str, str],
) -> DockerRunResult:
    stop_container(name)
    remove_container(name)

    docker_cmd = [
        "docker", "run", "--rm",
        "--name", name,
    ]
    for host_path, container_path in volumes.items():
        docker_cmd.extend(["-v", f"{host_path}:{container_path}"])
    for key, value in env.items():
        docker_cmd.extend(["-e", f"{key}={value}"])
    docker_cmd.append(image)
    docker_cmd.extend(command)

    result = _run_command(docker_cmd)
    return DockerRunResult(
        returncode=result.returncode,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
    )
