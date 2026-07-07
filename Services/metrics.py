# Services/metrics.py
from Core.config import settings
from Database.database import get_queue_metrics
from Services.alerts import send_critical_alert
from Services.logger import log_system_event, logger


def evaluate_queue_health() -> dict:
    metrics = get_queue_metrics()
    alerts = []

    if metrics["held_for_review"] >= settings.METRICS_ALERT_HELD_THRESHOLD:
        message = (
            f"Held orders threshold reached: {metrics['held_for_review']} "
            f"(threshold={settings.METRICS_ALERT_HELD_THRESHOLD})"
        )
        alerts.append(message)
        log_system_event(component="METRICS", status="HELD_THRESHOLD", message=message)
        send_critical_alert("QUEUE_HEALTH", message)

    if metrics["in_flight"] > 50:
        message = f"High in-flight queue volume detected: {metrics['in_flight']}"
        alerts.append(message)
        logger.warning(message)

    return {
        "metrics": metrics,
        "alerts": alerts,
        "healthy": len(alerts) == 0,
    }
