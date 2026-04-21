# -*- coding: utf-8 -*-
import logging
import re
import lxml.etree as _lxml_etree

_logger = logging.getLogger(__name__)
_logger.info('edoc_ds_patch fromstring carregado')

try:
    import erpbrasil.edoc.edoc as edoc_module
except ImportError:
    edoc_module = None

try:
    import erpbrasil.edoc.nfe as nfe_module
except ImportError:
    nfe_module = None

_ORIGINAL_FROMSTRING = _lxml_etree.fromstring


def _corrigir_namespace_ds(xml_content):
    if isinstance(xml_content, bytes):
        xml_str = xml_content.decode('utf-8')
        is_bytes = True
    else:
        xml_str = xml_content
        is_bytes = False

    if '<ds:Signature' not in xml_str:
        return xml_content

    if 'xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' in xml_str or "xmlns:ds='http://www.w3.org/2000/09/xmldsig#'" in xml_str:
        return xml_content

    # Separar declaração XML
    xml_decl_match = re.match(r'(<\?xml[^>]*\?>)?(.*)', xml_str, re.DOTALL)
    xml_decl = xml_decl_match.group(1) or ''
    body = xml_decl_match.group(2)

    # Localizar primeira tag de abertura
    tag_match = re.search(r'(<[^/][^>]*>)', body)
    if not tag_match:
        return xml_content

    tag = tag_match.group(1)

    # Verificar se já tem xmlns:ds
    if 'xmlns:ds=' in tag:
        return xml_content

    # Injetar antes de >
    new_tag = tag[:-1] + ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
    corrected_body = body.replace(tag, new_tag, 1)
    corrected_xml = xml_decl + corrected_body

    _logger.info('Namespace ds corrigido no fromstring')

    if is_bytes:
        return corrected_xml.encode('utf-8')
    return corrected_xml


def _safe_fromstring(value, *args, **kwargs):
    try:
        return _ORIGINAL_FROMSTRING(value, *args, **kwargs)
    except _lxml_etree.XMLSyntaxError as e:
        if 'Namespace prefix ds on Signature is not defined' in str(e):
            _logger.info('Entrando na correção de namespace em fromstring')
            corrected_value = _corrigir_namespace_ds(value)
            return _ORIGINAL_FROMSTRING(corrected_value, *args, **kwargs)
        else:
            raise


_EDOC_DS_PATCH_APPLIED = False
if not _EDOC_DS_PATCH_APPLIED:
    if edoc_module and hasattr(edoc_module, 'etree'):
        edoc_module.etree.fromstring = _safe_fromstring
        _logger.info('Patch fromstring aplicado em erpbrasil.edoc.edoc')
    if nfe_module and hasattr(nfe_module, 'etree'):
        nfe_module.etree.fromstring = _safe_fromstring
        _logger.info('Patch fromstring aplicado em erpbrasil.edoc.nfe')
    _lxml_etree.fromstring = _safe_fromstring
    _logger.info('Patch fromstring aplicado em lxml.etree')
    _EDOC_DS_PATCH_APPLIED = True
