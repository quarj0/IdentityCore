import os

from common.configuration import validate_production_environment

from .base import *  # noqa: F401,F403

DEBUG = False

# Validate the raw environment rather than settings defaults: production must never
# silently inherit credentials intended only for local development.
validate_production_environment(os.environ)
