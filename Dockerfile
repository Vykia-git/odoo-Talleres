FROM odoo:19.0

USER root

# Instalamos las dependencias necesarias para los módulos de la OCA (como cssselect para resource_booking)
RUN pip install --no-cache-dir cssselect --break-system-packages

USER odoo
