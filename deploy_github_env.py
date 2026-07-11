#!/usr/bin/env python3
"""deploy_github_env.py: Push al repo usando token desde variable de entorno.
No escribe credenciales en archivos ni terminal."""
import os, subprocess, sys

REPO_DIR = os.path.expanduser("~/catedral/dashboard_43")

def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("ERROR: Exportar GITHUB_TOKEN antes de ejecutar")
        print("  export GITHUB_TOKEN='ghp_...'")
        print("  python3 deploy_github_env.py")
        sys.exit(1)

    remote_url = f"https://{token}@github.com/grupoepem-bi-team/dashboard_monitoreo_43.git"

    os.chdir(REPO_DIR)

    # Configurar identidad git
    subprocess.run(["git", "config", "user.name", "Grupo EPEM BI Team"], capture_output=True)
    subprocess.run(["git", "config", "user.email", "bi@grupoepem.com"], capture_output=True)

    # Remote
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    r = subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True, text=True)
    if r.returncode != 0 and "already exists" not in r.stderr:
        print(f"WARN remote: {r.stderr}")

    # Verificar (redactado)
    r = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
    safe = r.stdout.replace(token, "***")
    print("Remote:", safe.strip())

    # Push
    print("\nPusheando...")
    r = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr.replace(token, "***"))

    if r.returncode == 0:
        print("\n✅ Push exitoso!")
    else:
        print(f"\n❌ Error (code {r.returncode})")
        sys.exit(1)

if __name__ == "__main__":
    main()
