# -*- coding: utf-8 -*-
import os
import logging.config


import structlog

pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.

    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt='iso')
]

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=False),
            "foreign_pre_chain": pre_chain,
            "keep_exc_info": True,
            "keep_stack_info": True
        },
        "colored": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": pre_chain,
            "keep_exc_info": True,
            "keep_stack_info": True
        },
    },
    "handlers": {
        "default": {
            "level": os.environ.get('LOG_LEVEL','DEBUG'),
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": os.environ.get('LOG_LEVEL','DEBUG'),
            "propagate": True,
        },
    }
})
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
