# +++++++++++ DJANGO +++++++++++
# Django WSGI configuration for PythonAnywhere
#
# This file contains the WSGI configuration required to serve up your
# Django application on PythonAnywhere.
#
# To use this file, install your Django project into your PythonAnywhere home directory:
#   cd ~
#   git clone https://github.com/yourusername/erp-system.git
#
# Then configure this file in the PythonAnywhere web app settings:
#   Source code: /home/yourusername/erp-system/factory_erp
#   WSGI config file: /home/yourusername/erp-system/pythonanywhere_wsgi.py

import os
import sys

# === ВАЖНО: Замените 'yourusername' на ваше имя пользователя PythonAnywhere ===
path = '/home/yourusername/erp-system/factory_erp'
if path not in sys.path:
    sys.path.insert(0, path)

# Установить настройки Django для production
os.environ['DJANGO_SETTINGS_MODULE'] = 'factory_erp.settings_pythonanywhere'

# Активировать виртуальное окружение (если используется)
# VENV_PATH = '/home/yourusername/erp-system/venv'
# activate_this = os.path.join(VENV_PATH, 'bin', 'activate_this.py')
# with open(activate_this) as f:
#     exec(f.read(), {'__file__': activate_this})

# Импортировать Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

