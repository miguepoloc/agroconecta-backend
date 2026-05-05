"""AWS Lambda entry point via Mangum adapter."""

import mangum

from src.entrypoints import app as app_module

handler = mangum.Mangum(app_module.app, lifespan="off")
