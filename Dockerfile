FROM odoo:19.0

USER root

# Instalamos las dependencias necesarias para los módulos de la OCA (como cssselect para resource_booking)
RUN pip install --no-cache-dir cssselect --break-system-packages

# Dependencias Python para localización española (AEAT/SII), SEPA y contabilidad OCA:
#   zeep, requests        -> l10n_es_aeat_sii_oca (envío SII a la AEAT)
#   unidecode             -> l10n_es_aeat, account_banking_pain_base (SEPA)
#   num2words             -> impresión de importes en letra (cheques/pagos)
#   pycountry             -> l10n_es_facturae
#   chardet               -> importación de extractos N43
#   python-dateutil       -> account_asset_management (amortización de activos)
RUN pip install --no-cache-dir \
    zeep requests unidecode num2words pycountry chardet python-dateutil \
    --break-system-packages

USER odoo
