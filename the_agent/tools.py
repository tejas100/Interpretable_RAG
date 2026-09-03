GET_METRICS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_metrics",
        "description": (
            "Fetch time-series latency (p50/p99 in ms) and error rate (%) "
            "for a given service over a recent time window. Use this to "
            "check whether a service is currently degraded."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["api-gateway", "auth-service", "orders-service", "payments-service"],
                    "description": "The service to fetch metrics for."
                },
                "minutes": {
                    "type": "integer",
                    "description": "How many minutes of recent history to fetch.",
                    "default": 15
                }
            },
            "required": ["service"]
        }
    }
}