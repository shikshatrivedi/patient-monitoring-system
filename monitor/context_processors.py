"""
Context processor that injects hardware config and status into every template.
This makes {{ hw_config.port }}, {{ hw_status.is_connected }} etc.
available globally without needing to pass them from every view.
"""


def hardware_context(request):
    """
    Inject HardwareConfig and HardwareStatus into every template context.
    Wrapped in try/except so the site works even before migrations are run.
    """
    try:
        from monitor.models import HardwareConfig, HardwareStatus
        from django.utils import timezone
        config = HardwareConfig.get_config()
        status = HardwareStatus.get_status()
        
        # Real connection logic: connected=True AND last_seen < 5s
        is_connected = False
        if status.connected and status.last_seen:
            diff = timezone.now() - status.last_seen
            if diff.total_seconds() < 5:
                is_connected = True

        return {
            'hw_config': config,
            'hw_status': status,
            'hw_port': config.port,
            'hw_connected': is_connected,
        }
    except Exception:
        return {
            'hw_config': None,
            'hw_status': None,
            'hw_port': 'N/A',
            'hw_connected': False,
        }
