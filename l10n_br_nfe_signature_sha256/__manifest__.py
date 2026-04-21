{
    "name": "l10n_br_nfe_cert_sha256",
    "version": "16.0.1.0.0",
    "category": "Localization",
    "summary": "Adapta novos certificados SHA256 para assinar os documentos.",
    "description": """
        Módulo que adapta a assinatura de documentos fiscais com certificado SHA256.
        Detecta automaticamente qual modelo de certificado e caso for tipo SHA256, entrega o
        documento com formato SHA1. E deixa pronto para migração futura para formato SHA256.
        """,
    "author": "MadooIT",
    "license": "AGPL-3",
    "depends": ["l10n_br_nfe", "account"],
    "external_dependencies": {
        "python": ["erpbrasil.assinatura", "signxml", "cryptography", "lxml"],
    },
    "data": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init_hook",
}
