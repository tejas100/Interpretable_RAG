"""
Telemetry query functions. These are what the agent's tools will eventually
call. Each function reads simulator._TRUE_STATE indirectly (through the
scenario logic below) and returns data shaped like real observability
output — never ground truth directly.
"""

import random
import time

from simulator import (
    ServiceName,
    IncidentType,
    get_true_state,
    get_deploy_history,
    _services_downstream_distance,
)

random.seed()  # real randomness; set a fixed seed in tests for determinism


def get_metrics(service: ServiceName, minutes: int = 15) -> dict:
    """
    Returns time-bucketed p50/p99 latency (ms) and error rate (%) for the
    last `minutes` minutes, one point per minute.
    """
    state = get_true_state()
    now = time.time()
    points = []

    for i in range(minutes, 0, -1):
        ts = now - i * 60
        p50, p99, err_rate = 40.0, 120.0, 0.5  # healthy baseline w/ noise

        if state.incident_type == IncidentType.BAD_DEPLOY:
            dist = _services_downstream_distance(service, state.affected_service)
            if dist is not None and ts >= state.incident_start_time:
                if dist == 0:
                    p50, p99, err_rate = 45.0, 140.0, 18.0  # origin: fast failures, latency near-normal
                else:
                    # errors propagate upstream through the call chain, attenuating slightly;
                    # latency barely moves, since these are fast exceptions, not timeouts —
                    # THIS is the signature that should let the agent tell bad_deploy apart
                    # from downstream_timeout even though both raise upstream error rates.
                    factor = max(0.2, 1.0 - 0.25 * dist)
                    p50 = 40.0 + 8.0 * factor
                    p99 = 120.0 + 25.0 * factor
                    err_rate = 0.5 + (18.0 - 0.5) * factor

        elif state.incident_type == IncidentType.DOWNSTREAM_TIMEOUT:
            dist = _services_downstream_distance(service, state.affected_service)
            if dist is not None and ts >= state.incident_start_time:
                if dist == 0:
                    p50, p99, err_rate = 800.0, 3500.0, 35.0  # the failing service itself
                else:
                    # attenuates as you move upstream, but never fully healthy
                    factor = max(0.15, 1.0 - 0.3 * dist)
                    p50 = 40.0 + (800.0 - 40.0) * factor
                    p99 = 120.0 + (3500.0 - 120.0) * factor
                    err_rate = 0.5 + (35.0 - 0.5) * factor

        # noise so it "looks real" — no two points identical
        p50 *= random.uniform(0.9, 1.1)
        p99 *= random.uniform(0.85, 1.15)
        err_rate = max(0.0, err_rate * random.uniform(0.8, 1.2))

        points.append({
            "timestamp": ts,
            "p50_latency_ms": round(p50, 1),
            "p99_latency_ms": round(p99, 1),
            "error_rate_pct": round(err_rate, 2),
        })

    return {"service": service.value, "window_minutes": minutes, "points": points}


def get_logs(service: ServiceName, minutes: int = 15, limit: int = 50) -> list[dict]:
    """Returns recent log lines, newest first. Injects error-level lines during incidents."""
    state = get_true_state()
    now = time.time()
    logs = []

    baseline_msgs = [
        "request completed",
        "cache hit for key",
        "health check ok",
    ]

    is_incident_active = False
    error_msg = None

    if state.incident_type == IncidentType.BAD_DEPLOY:
        dist = _services_downstream_distance(service, state.affected_service)
        if dist is not None:
            is_incident_active = True
            if dist == 0:
                error_msg = f"NullPointerException in OrderValidator (deploy {state.bad_deploy_version})"
            else:
                error_msg = f"received 500 from downstream call to {state.affected_service.value}"

    elif state.incident_type == IncidentType.DOWNSTREAM_TIMEOUT:
        dist = _services_downstream_distance(service, state.affected_service)
        if dist is not None:
            is_incident_active = True
            if dist == 0:
                error_msg = "connection pool exhausted, rejecting new requests"
            else:
                error_msg = f"timeout waiting for downstream call to {state.affected_service.value} (5000ms exceeded)"

    n = min(limit, minutes * 4)
    for i in range(n):
        ts = now - random.uniform(0, minutes * 60)
        if (
            is_incident_active
            and ts >= state.incident_start_time
            and random.random() < 0.4
        ):
            logs.append({"timestamp": ts, "level": "ERROR", "service": service.value, "message": error_msg})
        else:
            logs.append({
                "timestamp": ts,
                "level": "INFO",
                "service": service.value,
                "message": random.choice(baseline_msgs),
            })

    logs.sort(key=lambda l: l["timestamp"], reverse=True)
    return logs


def get_traces(service: ServiceName, minutes: int = 15, limit: int = 10) -> list[dict]:
    """
    Returns recent distributed traces touching `service` — a list of spans
    showing the call chain and per-hop latency. During downstream_timeout,
    traces that reach the failing service show a long span there.
    """
    from simulator import SERVICE_DEPENDENCIES

    state = get_true_state()
    now = time.time()
    traces = []

    def build_chain(start: ServiceName) -> list[ServiceName]:
        chain = [start]
        current = start
        while SERVICE_DEPENDENCIES.get(current):
            current = SERVICE_DEPENDENCIES[current][0]
            chain.append(current)
        return chain

    chain = build_chain(service)

    for i in range(limit):
        ts = now - random.uniform(0, minutes * 60)
        spans = []
        incident_live = (
            state.incident_type == IncidentType.DOWNSTREAM_TIMEOUT
            and ts >= (state.incident_start_time or 0)
        )
        for hop in chain:
            base_ms = random.uniform(5, 20)
            if incident_live and hop == state.affected_service:
                base_ms = random.uniform(2500, 5000)  # the actual slow hop
            elif incident_live and _services_downstream_distance(hop, state.affected_service) not in (None, 0):
                base_ms += random.uniform(50, 300)  # waiting on downstream
            spans.append({"service": hop.value, "duration_ms": round(base_ms, 1)})

        traces.append({
            "trace_id": f"trc-{int(ts)}-{i}",
            "timestamp": ts,
            "root_service": service.value,
            "total_duration_ms": round(sum(s["duration_ms"] for s in spans), 1),
            "spans": spans,
        })

    traces.sort(key=lambda t: t["timestamp"], reverse=True)
    return traces


def get_deployment_history(service: ServiceName) -> list[dict]:
    """Thin passthrough — kept here so all telemetry access goes through one module."""
    return get_deploy_history(service)