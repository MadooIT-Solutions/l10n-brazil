ARQUIVO: models/erpbrasil_sha1_patch.py

import logging

_logger = logging.getLogger(__name__)

# Tentar importar Assinador de caminhos compatíveis
try:
    from erpbrasil.assinatura import Assinador as ERPAssinador
except ImportError:
    try:
        from erpbrasil.assinatura.assinatura import Assinador as ERPAssinador
    except ImportError:
        _logger.warning("Não foi possível importar Assinador do erpbrasil. Patch não aplicado.")
        ERPAssinador = None

if ERPAssinador:
    # Classe de patch para forçar SHA-1
    class AssinadorSHA1Patch:
        def __init__(self, *args, **kwargs):
            self.original_assinador = ERPAssinador(*args, **kwargs)

        def assina_xml(self, *args, **kwargs):
            # Wrapper para assina_xml, se existir
            if hasattr(self.original_assinador, 'assina_xml'):
                return self._patch_assina_xml(*args, **kwargs)
            else:
                raise AttributeError("Método assina_xml não encontrado.")

        def assina_xml2(self, *args, **kwargs):
            # Wrapper para assina_xml2, se existir
            if hasattr(self.original_assinador, 'assina_xml2'):
                return self._patch_assina_xml(*args, **kwargs)
            else:
                raise AttributeError("Método assina_xml2 não encontrado.")

        def assina_nfse(self, *args, **kwargs):
            # Wrapper para assina_nfse, se existir
            if hasattr(self.original_assinador, 'assina_nfse'):
                return self._patch_assina_nfse(*args, **kwargs)
            else:
                raise AttributeError("Método assina_nfse não encontrado.")

        def _patch_assina_xml(self, xml_string, certificado, senha, id_tag=None):
            # Lógica de patch para assina_xml e assina_xml2
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import pkcs12
            import xml.etree.ElementTree as ET
            from signxml import XMLSigner, methods
            from lxml import etree

            # Carregar certificado PFX
            p12 = pkcs12.load_key_and_certificates(certificado, senha.encode())
            private_key = p12[0]
            certificate = p12[1]

            # Converter para PEM
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)

            # Parse XML
            root = etree.fromstring(xml_string.encode('utf-8'))

            # Encontrar elemento alvo com XPath por local-name
            if id_tag is None:
                id_tag = 'infNFe'  # Padrão para NF-e
            xpath = f".//*[local-name()='{id_tag}']"
            element = root.xpath(xpath, namespaces={})[0]

            # Descobrir reference_uri do atributo Id ou id
            reference_uri = None
            if 'Id' in element.attrib:
                reference_uri = '#' + element.attrib['Id']
            elif 'id' in element.attrib:
                reference_uri = '#' + element.attrib['id']
            else:
                reference_uri = ''  # Ou None, dependendo da implementação

            # Assinar com SHA-1
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha1",
                digest_algorithm="sha1",
                c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
            )
            signed_xml = signer.sign(
                root,
                key=private_key_pem,
                cert=certificate_pem,
                reference_uri=reference_uri
            )

            return etree.tostring(signed_xml, encoding='unicode')

        def _patch_assina_nfse(self, xml_string, certificado, senha, id_tag=None):
            # Lógica de patch para assina_nfse
            if id_tag is None:
                id_tag = 'InfDeclaracaoPrestacaoServico'
            return self._patch_assina_xml(xml_string, certificado, senha, id_tag)

    # Aplicar patch: substituir Assinador pela versão patched
    import erpbrasil.assinatura
    erpbrasil.assinatura.Assinador = AssinadorSHA1Patch

ARQUIVO: models/assinador_auto.py (somente método _assinar_signxml)

    def _assinar_signxml(self, xml_string, certificado, senha, id_tag=None):
        # Método corrigido para forçar SHA-1
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import pkcs12
        import xml.etree.ElementTree as ET
        from signxml import XMLSigner, methods
        from lxml import etree

        # Carregar certificado PFX
        p12 = pkcs12.load_key_and_certificates(certificado, senha.encode())
        private_key = p12[0]
        certificate = p12[1]

        # Converter para PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)

        # Parse XML
        root = etree.fromstring(xml_string.encode('utf-8'))

        # Encontrar elemento alvo com XPath por local-name
        if id_tag is None:
            id_tag = 'infNFe'  # Padrão para NF-e
        xpath = f".//*[local-name()='{id_tag}']"
        element = root.xpath(xpath, namespaces={})[0]

        # Descobrir reference_uri do atributo Id ou id
        reference_uri = None
        if 'Id' in element.attrib:
            reference_uri = '#' + element.attrib['Id']
        elif 'id' in element.attrib:
            reference_uri = '#' + element.attrib['id']
        else:
            reference_uri = ''

        # Assinar com SHA-1
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        signed_xml = signer.sign(
            root,
            key=private_key_pem,
            cert=certificate_pem,
            reference_uri=reference_uri
        )

        return etree.tostring(signed_xml, encoding='unicode')

