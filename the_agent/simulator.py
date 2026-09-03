"""
Fake production system simulator.

Models a small chain of services with realistic dependencies, and can be
told to "inject" an incident scenario. Once injected, all telemetry query
functions (logs/metrics/traces/deploy history) return data CONSISTENT with
that incident, the way real observability tools reflect ground truth without
revealing it directly.

The agent that investigates this system NEVER reads `_TRUE_STATE` directly —
it only calls the query functions in telemetry.py, exactly like a real
on-call engineer only has logs/metrics/traces, not god-mode access to what's
actually wrong.
"""

import random
import time
from dataclasses import dataclass, field
from enum import Enum


class ServiceName(str, Enum):
    API_GATEWAY = "api-gateway"
    AUTH_SERVICE = "auth-service"
    ORDERS_SERVICE = "orders-service"
    PAYMENTS_SERVICE = "payments-service"


# Linear dependency chain: api-gateway -> auth -> orders -> payments
SERVICE_DEPENDENCIES = {
    ServiceName.API_GATEWAY: [ServiceName.AUTH_SERVICE],
    ServiceName.AUTH_SERVICE: [ServiceName.ORDERS_SERVICE],
    ServiceName.ORDERS_SERVICE: [ServiceName.PAYMENTS_SERVICE],
    ServiceName.PAYMENTS_SERVICE: [],
}


class IncidentType(str, Enum):
    NONE = "none"
    BAD_DEPLOY = "bad_deploy"
    DOWNSTREAM_TIMEOUT = "downstream_timeout"


@dataclass
class TrueState:
    """Ground truth. The agent never sees this directly."""
    incident_type: IncidentType = IncidentType.NONE
    affected_service: ServiceName | None = None
    incident_start_time: float | None = None
    # bad_deploy specifics
    bad_deploy_version: str | None = None
    # downstream_timeout specifics
    upstream_service: ServiceName | None = None  # the one that SEES the symptom


_TRUE_STATE = TrueState()

# Fixed deployment history so "deploy correlation" is a real, checkable fact
_DEPLOY_HISTORY: dict[ServiceName, list[dict]] = {
    svc: [] for svc in ServiceName
}


def reset():
    """Reset to healthy baseline. Call this between scenario runs."""
    global _TRUE_STATE
    _TRUE_STATE = TrueState()
    now = time.time()
    for svc in ServiceName:
        _DEPLOY_HISTORY[svc] = [
            {"version": "v1.0.0", "timestamp": now - 3600 * 24 * 3, "author": "ci-bot"},
            {"version": "v1.0.1", "timestamp": now - 3600 * 24, "author": "ci-bot"},
        ]


def inject_bad_deploy(service: ServiceName, minutes_ago: float = 5.0):
    """Simulate: a bad deploy went out to `service` and started throwing errors."""
    global _TRUE_STATE
    now = time.time()
    deploy_time = now - minutes_ago * 60
    version = "v1.0.2-canary"
    _DEPLOY_HISTORY[service].append(
        {"version": version, "timestamp": deploy_time, "author": "jsmith"}
    )
    _TRUE_STATE = TrueState(
        incident_type=IncidentType.BAD_DEPLOY,
        affected_service=service,
        incident_start_time=deploy_time,
        bad_deploy_version=version,
    )


def inject_downstream_timeout(failing_service: ServiceName, minutes_ago: float = 5.0):
    """
    Simulate: `failing_service` starts timing out / degrading, with NO deploy
    correlation. Every service upstream of it (per SERVICE_DEPENDENCIES) will
    show elevated latency and timeout errors, worst near the failure and
    attenuating as you move further upstream.
    """
    global _TRUE_STATE
    now = time.time()
    start = now - minutes_ago * 60
    _TRUE_STATE = TrueState(
        incident_type=IncidentType.DOWNSTREAM_TIMEOUT,
        affected_service=failing_service,
        incident_start_time=start,
        upstream_service=failing_service,
    )


def get_true_state() -> TrueState:
    """FOR TEST/DEBUG USE ONLY. The agent must never call this."""
    return _TRUE_STATE


def get_deploy_history(service: ServiceName) -> list[dict]:
    return list(_DEPLOY_HISTORY.get(service, []))


def _services_downstream_distance(from_service: ServiceName, to_service: ServiceName) -> int | None:
    """BFS distance along SERVICE_DEPENDENCIES; None if unreachable."""
    if from_service == to_service:
        return 0
    frontier = [(from_service, 0)]
    seen = {from_service}
    while frontier:
        current, dist = frontier.pop(0)
        for dep in SERVICE_DEPENDENCIES.get(current, []):
            if dep == to_service:
                return dist + 1
            if dep not in seen:
                seen.add(dep)
                frontier.append((dep, dist + 1))
    return None