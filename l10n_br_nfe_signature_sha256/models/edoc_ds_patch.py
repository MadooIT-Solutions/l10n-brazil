# edoc_ds_patch.py - Patch para correção de namespace ds e estrutura XML em Odoo 16 CE

import logging
import io
import re
import inspect
from lxml import etree

_logger = logging.getLogger(__name__)

_logger.info("edoc_ds_patch v2 carregado")

# Importações defensivas
try:
    from erpbrasil.edoc import edoc
    _edoc_module = edoc
except ImportError:
    _edoc_module = None
    _logger.warning("Módulo erpbrasil.edoc.edoc não encontrado")

try:
    from erpbrasil.edoc import nfe
    _nfe_module = nfe
except ImportError:
    _nfe_module = None
    _logger.warning("Módulo erpbrasil.edoc.nfe não encontrado")

# Função helper para corrigir namespace ds
def _corrigir_namespace_ds(xml_content):
    """
    Corrige o namespace ds no XML se necessário.
    """
    if isinstance(xml_content, bytes):
        xml_str = xml_content.decode('utf-8')
        is_bytes = True
    else:
        xml_str = xml_content
        is_bytes = False

    # Verificar se já tem ds:Signature
    if '<ds:Signature' not in xml_str:
        return xml_content

    # Verificar se já tem xmlns:ds
    if 'xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' in xml_str or "xmlns:ds='http://www.w3.org/2000/09/xmldsig#'" in xml_str:
        return xml_content

    # Preservar declaração XML
    xml_declaration = ''
    if xml_str.startswith('<?xml'):
        match = re.match(r'(<\?xml[^>]*\?>)', xml_str)
        if match:
            xml_declaration = match.group(1)
            xml_str = xml_str[match.end():].lstrip()

    # Injetar xmlns:ds no primeiro elemento
    match = re.search(r'(<[^>]+>)', xml_str)
    if match:
        tag_start = match.group(1)
        if ' ' in tag_start:
            # Já tem atributos
            corrected_tag = tag_start[:-1] + ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' + tag_start[-1:]
        else:
            # Sem atributos
            corrected_tag = tag_start[:-1] + ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#"' + tag_start[-1:]
        xml_str = xml_str.replace(tag_start, corrected_tag, 1)
        _logger.info("Namespace ds corrigido no XML")

    result = xml_declaration + xml_str
    return result.encode('utf-8') if is_bytes else result

# Função helper para exportar objeto generateds
def _exportar_generateds(edoc_obj):
    """
    Exporta o objeto edoc para XML usando métodos disponíveis.
    """
    buffer = io.StringIO()
    try:
        # Tentar export com nível 0
        edoc_obj.export(buffer, 0)
    except (AttributeError, TypeError):
        try:
            # Tentar export sem nível
            edoc_obj.export(buffer)
        except (AttributeError, TypeError):
            if hasattr(edoc_obj, 'to_xml'):
                # Usar to_xml se disponível
                xml_str = edoc_obj.to_xml()
                buffer.write(xml_str)
            else:
                raise Exception("Não foi possível exportar o objeto edoc. Nenhum método de exportação encontrado.")
    return buffer.getvalue().encode('utf-8')

# Método patchado
def _patched_generateds_to_string_etree(self, edoc_obj, *args, **kwargs):
    """
    Método patchado para _generateds_to_string_etree.
    """
    try:
        # Exportar o objeto
        contents = _exportar_generateds(edoc_obj)
        # Corrigir namespace ds
        contents_corrigido = _corrigir_namespace_ds(contents)
        # Parsear para etree
        xml_tree = etree.fromstring(contents_corrigido)
        return (contents_corrigido, xml_tree)
    except Exception as e:
        _logger.error(f"Falha no patch: {str(e)}")
        # Fallback para método original se salvo
        if hasattr(self, '_original_generateds_to_string_etree'):
            _logger.info("Tentando fallback para método original")
            try:
                return self._original_generateds_to_string_etree(edoc_obj, *args, **kwargs)
            except Exception as e2:
                _logger.error(f"Fallback também falhou: {str(e2)}")
                raise e
        else:
            raise e

# Descobrir e aplicar patches
def _aplicar_patches():
    """
    Descobre classes com _generateds_to_string_etree e aplica o patch.
    """
    modules = [_edoc_module, _nfe_module]
    patched_classes = []
    for module in modules:
        if module is None:
            continue
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, '_generateds_to_string_etree'):
                if not hasattr(obj, '_patched_by_edoc_ds_patch'):
                    # Salvar método original
                    obj._original_generateds_to_string_etree = obj._generateds_to_string_etree
                    # Aplicar patch
                    obj._generateds_to_string_etree = _patched_generateds_to_string_etree
                    obj._patched_by_edoc_ds_patch = True
                    patched_classes.append(name)
                    _logger.info(f"Patch aplicado na classe {name}")
                else:
                    _logger.info(f"Classe {name} já patchada, pulando")
    if patched_classes:
        _logger.info(f"Classes encontradas e patchadas: {', '.join(patched_classes)}")
    else:
        _logger.warning("Nenhuma classe com _generateds_to_string_etree encontrada")

# Aplicar patches ao importar
_aplicar_patches()
