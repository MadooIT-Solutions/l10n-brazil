from odoo import models, api
import logging
import base64
from lxml import etree
from .assinador_auto import AssinadorAuto

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_br_nfe_sign_xml(self, xml_content):
        try:
            company = self.company_id or self.env.company
            if not company.l10n_br_certificate:
                raise ValueError('Certificado não configurado para a empresa.')
            if not company.l10n_br_certificate_password:
                raise ValueError('Senha do certificado não configurada para a empresa.')

            cert_input = base64.b64decode(company.l10n_br_certificate)
            cert_password = company.l10n_br_certificate_password

            assinador = AssinadorAuto(cert_input, cert_password)
            xml_assinado = assinador.assinar(xml_content, id_element='infNFe')

            if isinstance(xml_assinado, str):
                xml_assinado = xml_assinado.encode('utf-8')

            # Diagnóstico de validade do XML assinado
            tem_signature = b'<ds:Signature' in xml_assinado
            tem_namespace = b'xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' in xml_assinado or b"xmlns:ds='http://www.w3.org/2000/09/xmldsig#'" in xml_assinado
            _logger.info(f'XML assinado tem <ds:Signature>: {tem_signature}')
            _logger.info(f'XML assinado tem namespace ds: {tem_namespace}')

            try:
                etree.fromstring(xml_assinado)
                _logger.info('XML assinado é válido e parseável.')
            except etree.XMLSyntaxError as e:
                trecho_inicial = xml_assinado[:1200].decode('utf-8', errors='ignore')
                _logger.error(f'Erro de sintaxe no XML assinado: {e}')
                _logger.error(f'Trecho inicial do XML: {trecho_inicial}')

            return xml_assinado
        except Exception as e:
            _logger.error(f'Erro ao assinar XML: {e}')
            return xml_content
