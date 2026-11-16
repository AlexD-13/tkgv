import logging
import logging.config
import json
import os

def setup_logging():
    """Configura el logging para toda la aplicación"""
    
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(levelname)s\t | %(asctime)s | %(name)s | %(message)s"
            },
            "detailed": {
                "format": "%(levelname)s\t | %(asctime)s | %(name)s | %(module)s:%(lineno)d | %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
    
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(log_config)