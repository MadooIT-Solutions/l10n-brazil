# -*- coding: utf-8 -*-
"""Módulo para assinatura automática de XMLs em Odoo 16 CE com integração OCA l10n-brazil."""

import logging
import os
import tempfile
import base64
import re
from lxml import etree

try:
    from erpbrasil.assinatura import Assinador as ErpbrassilAssinatura
    ERPBRASIL_AVAILABLE = True
except ImportError:
    ERPBRASIL_AVAILABLE = False

try:
    from signxml import XMLSigner, methods
    SIGNXML_AVAILABLE = True
except ImportError:
    SIGNXML_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

_logger = logging.getLogger(__name__)


class AssinadorAuto:
    def __init__(self, certificado_path, password):
        self.certificado_path = certificado_path
        self.password = password
        self._modulo_usado = None
        self._detectar_modulo()

    def _prepare_certificate(self, cert_input):
        if os.path.isfile(cert_input):
            return cert_input
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pfx') as temp_file:
            if isinstance(cert_input, str):
                cert_bytes = base64.b64decode(cert_input)
            else:
                cert_bytes = cert_input
            temp_file.write(cert_bytes)
            return temp_file.name

    def _detectar_modulo(self):
        if ERPBRASIL_AVAILABLE:
            self._modulo_usado = 'erpbrasil'
        elif SIGNXML_AVAILABLE and CRYPTOGRAPHY_AVAILABLE:
            self._modulo_usado = 'signxml'
        else:
            raise ImportError("Nenhum módulo de assinatura disponível: erpbrasil ou signxml com cryptography.")

    @property
    def modulo_usado(self):
        return self._modulo_usado

    def assinar(self, xml_content, id_element='infNFe'):
        if isinstance(xml_content, str):
            xml_bytes = xml_content.encode('utf-8')
        else:
            xml_bytes = xml_content
        _logger.info(f"Assinando XML usando módulo: {self._modulo_usado}")
        if self._modulo_usado == 'erpbrasil':
            return self._assinar_erpbrasil(xml_bytes, id_element)
        elif self._modulo_usado == 'signxml':
            return self._assinar_signxml(xml_bytes, id_element)

    def _garantir_namespace_ds(self, xml_content):
        if isinstance(xml_content, str):
            xml_str = xml_content
        else:
            xml_str = xml_content.decode('utf-8')
        if '<ds:Signature' not in xml_str:
            return xml_content if isinstance(xml_content, bytes) else xml_str.encode('utf-8')
        if 'xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' in xml_str or "xmlns:ds='http://www.w3.org/2000/09/xmldsig#'" in xml_str:
            return xml_content if isinstance(xml_content, bytes) else xml_str.encode('utf-8')
        xml_declaration = ''
        match = re.match(r'(<\?xml[^>]*\?>)?(.*)', xml_str, re.DOTALL)
        if match:
            xml_declaration = match.group(1) or ''
            body = match.group(2)
        else:
            body = xml_str
        match_element = re.search(r'(<[^>]+>)', body)
        if match_element:
            tag_start = match_element.group(1)
            if 'xmlns:ds' not in tag_start:
                new_tag_start = tag_start[:-1] + ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' + tag_start[-1]
                body = body.replace(tag_start, new_tag_start, 1)
                _logger.info("Namespace ds injetado no primeiro elemento.")
        result_str = xml_declaration + body
        return result_str.encode('utf-8')

    def _assinar_signxml(self, xml_bytes, id_element):
        signature_algorithm = 'rsa-sha1'
        digest_algorithm = 'sha1'
        with open(self.certificado_path, 'rb') as f:
            pfx_data = f.read()
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(pfx_data, self.password.encode('utf-8'))
        if not private_key or not certificate:
            raise ValueError("Certificado inválido ou senha incorreta.")
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        root = etree.fromstring(xml_bytes)
        elemento_alvo = root.xpath(f"//*[local-name()='{id_element}']")
        if not elemento_alvo:
            raise ValueError(f"Elemento {id_element} não encontrado.")
        elemento_alvo = elemento_alvo[0]
        valor_id = elemento_alvo.get('Id') or elemento_alvo.get('id')
        if not valor_id:
            raise ValueError("Atributo Id ou id não encontrado no elemento alvo.")
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm=signature_algorithm,
            digest_algorithm=digest_algorithm,
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )
        signed_root = signer.sign(root, key=key_pem, cert=cert_pem, reference_uri=f'#{valor_id}')
        xml_assinado = etree.tostring(signed_root, encoding='utf-8', xml_declaration=True)
        return self._garantir_namespace_ds(xml_assinado)

    def _assinar_erpbrasil(self, xml_bytes, id_element):
        root = etree.fromstring(xml_bytes)
        elemento_alvo = root.xpath(f"//*[local-name()='{id_element}']")
        if not elemento_alvo:
            raise ValueError(f"Elemento {id_element} não encontrado.")
        elemento_alvo = elemento_alvo[0]
        valor_id = elemento_alvo.get('Id') or elemento_alvo.get('id')
        if not valor_id:
            raise ValueError("Atributo Id ou id não encontrado no elemento alvo.")
        assinador = ErpbrassilAssinatura(self.certificado_path, self.password)
        xml_assinado = assinador.assina_xml(xml_bytes, id_tag=id_element, reference_uri=f'#{valor_id}')
        if isinstance(xml_assinado, str):
            xml_assinado = xml_assinado.encode('utf-8')
        return self._garantir_namespace_ds(xml_assinado)
