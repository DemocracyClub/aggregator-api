# asgi.py
import os

from django.core.asgi import get_asgi_application
from mangum import Mangum

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.settings")

application = get_asgi_application()

handler = Mangum(application, lifespan="off")
