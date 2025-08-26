from contextvars import ContextVar

# Context variable to store correlation IDs across async tasks
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    """Retrieve current correlation id or '-' if not set."""
    return correlation_id_var.get()
