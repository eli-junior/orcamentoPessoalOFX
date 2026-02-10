from decouple import config


ENVIRONMENT = (config("ENVIRONMENT")).lower()


match ENVIRONMENT:
    case "production":
        from .production import *  # noqa: F403
    case "development":
        from .development import *  # noqa: F403
    case _:
        raise ValueError(
            f"Unknown environment: {ENVIRONMENT}. Expected 'production' or 'development'."
        )