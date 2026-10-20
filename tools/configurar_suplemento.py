"""Gera os arquivos de implantação do suplemento Outlook com URLs/IDs reais.

Exemplo:
  python tools/configurar_suplemento.py --base-url https://assinaturas.exemplo.com \
    --client-id <GUID-DO-APP-REGISTRATION> --resource-uri api://<GUID-DO-APP-REGISTRATION> \
    --output-dir deploy-outlook
"""
import argparse
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="URL HTTPS pública, sem barra final")
    parser.add_argument("--client-id", required=True, help="Application (client) ID do Entra ID")
    parser.add_argument("--resource-uri", required=True, help="URI de recurso do app, conforme Entra ID")
    parser.add_argument("--output-dir", default="deploy-outlook", help="Pasta de saída")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        parser.error("--base-url deve ser uma URL HTTPS válida.")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        parser.error("--base-url deve conter somente origem, sem caminho, query ou fragmento.")
    try:
        uuid.UUID(args.client_id)
    except ValueError:
        parser.error("--client-id deve ser um GUID válido do Microsoft Entra ID.")
    if not args.resource_uri.startswith("api://"):
        parser.error("--resource-uri deve ser o URI de recurso configurado no Entra ID (normalmente api://...).")

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    static_out = out / "static" / "outlook_addin"
    static_out.mkdir(parents=True, exist_ok=True)

    replacements = {
        "{{BASE_URL}}": base_url,
        "{{BASE_HOST}}": parsed.hostname,
        "{{ADDIN_ID}}": str(uuid.uuid5(uuid.NAMESPACE_URL, base_url + "/outlook-signature-addin")),
        "{{CLIENT_ID}}": args.client_id,
        "{{RESOURCE_URI}}": args.resource_uri,
    }
    manifest = (ROOT / "outlook_addin" / "manifest.xml.template").read_text(encoding="utf-8")
    for old, new in replacements.items():
        manifest = manifest.replace(old, new)
    (out / "manifest.xml").write_text(manifest, encoding="utf-8")

    for source, name in [
        (ROOT / "outlook_addin" / "autorun.js.template", "autorun.js"),
        (ROOT / "outlook_addin" / "taskpane.js.template", "taskpane.js"),
        (ROOT / "outlook_addin" / "commands.js.template", "commands.js"),
    ]:
        content = source.read_text(encoding="utf-8").replace("{{BASE_URL}}", base_url)
        project_target = ROOT / "static" / "outlook_addin" / name
        project_target.write_text(content, encoding="utf-8")
        target = static_out / name
        target.write_text(content, encoding="utf-8")

    for name in ("autorun.html", "taskpane.html", "commands.html", "icon-32.png", "icon-80.png"):
        source = ROOT / "static" / "outlook_addin" / name
        if source.exists():
            shutil.copy2(source, static_out / name)

    # Validação sintática básica do XML produzido.
    import xml.etree.ElementTree as ET
    ET.parse(out / "manifest.xml")
    print(f"Manifesto gerado: {out / 'manifest.xml'}")
    print(f"Arquivos estáticos gerados: {static_out}")
    print(f"Os arquivos JS também foram configurados em: {ROOT / 'static' / 'outlook_addin'}")
    print("Reconstrua o executável após configurar os arquivos JS, se o próprio Flask for servir os arquivos do suplemento.")
    print("Antes da publicação, valide o manifesto no Microsoft 365 e confirme a configuração SSO do Entra ID.")


if __name__ == "__main__":
    main()
