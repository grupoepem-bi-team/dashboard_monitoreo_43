#!/usr/bin/env python3
"""deploy_github.py: Push del dashboard al repo remoto.
Lee token desde el Vault, no expone credenciales en terminal."""
import json, os, subprocess, sys

VAULT_PATH = os.path.expanduser("~/.hermes/vault/github_token.json")
REPO_DIR = os.path.expanduser("~/catedral/dashboard_43")
REPO_URL = "https://github.com/grupoepem-bi-team/dashboard_monitoreo_43.git"

def main():
    # Leer token del Vault
    with open(VAULT_PATH) as f:
        vault = json.load(f)
    token = vault.get("token", "")
    if not token:
        print("ERROR: No hay token en el Vault")
        sys.exit(1)

    # Configurar remote con token embebido (interno, no visible en terminal)
    remote_url = f"https://{token}@github.com/grupoepem-bi-team/dashboard_monitoreo_43.git"

    os.chdir(REPO_DIR)

    # Quitar remote anterior si existe
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)

    # Agregar remote
    r = subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True, text=True)
    if r.returncode != 0 and "already exists" not in r.stderr:
        print(f"ERROR agregando remote: {r.stderr}")
        sys.exit(1)

    # Verificar remote
    r = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
    print("Remote configurado:")
    print(r.stdout.replace(token, "***"))

    # Push
    print("\nPusheando a origin main...")
    r = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        # Redactar token del output
        safe_stderr = r.stderr.replace(token, "***")
        print(safe_stderr)

    if r.returncode == 0:
        print("\n✅ Push exitoso!")
    else:
        print(f"\n❌ Error en push (code {r.returncode})")
        sys.exit(1)

if __name__ == "__main__":
    main()
