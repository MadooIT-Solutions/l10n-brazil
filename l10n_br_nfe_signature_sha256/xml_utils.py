import logging
from lxml import etree

logger = logging.getLogger(__name__)


def ensure_ds_namespace(xml_content):
    """
    Garante que o namespace 'ds' esteja definido no elemento raiz do XML.
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode('utf-8')

    try:
        root = etree.fromstring(xml_content)
    except etree.XMLSyntaxError as e:
        logger.error(f"Erro ao parsear XML: {e}")
        raise

    nsmap = root.nsmap
    ds_ns = 'http://www.w3.org/2000/09/xmldsig#'

    if 'ds' in nsmap and nsmap['ds'] == ds_ns:
        logger.info("Namespace 'ds' já definido corretamente.")
        return etree.tostring(root, encoding='utf-8', xml_declaration=True)

    # Recriar o elemento raiz com nsmap atualizado
    new_nsmap = dict(nsmap)
    new_nsmap['ds'] = ds_ns

    new_root = etree.Element(root.tag, attrib=root.attrib, nsmap=new_nsmap)
    new_root.text = root.text
    new_root.tail = root.tail

    for child in root:
        new_root.append(child)

    logger.info("Namespace 'ds' adicionado ao elemento raiz.")
    return etree.tostring(new_root, encoding='utf-8', xml_declaration=True)

