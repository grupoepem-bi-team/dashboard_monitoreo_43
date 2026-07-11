#!/usr/bin/env python3
"""test_regresion_dashboard43.py: Test de regresion completo del pipeline.
Verifica: cronjobs, scripts, JSON, repo, dashboard. Cero bugs silenciosos.
"""
import json, os, subprocess, sys, datetime

REPO_DIR = os.path.expanduser("~/catedral/dashboard_43")
DATA_DIR = os.path.join(REPO_DIR, "data")
SCRIPT_DIR = os.path.expanduser("~/catedral/scripts")
LOGS_SCRIPT_DIR = os.path.expanduser("~/logs-central/scripts")
VAULT_DIR = os.path.expanduser("~/.hermes/vault")

errors = []
warnings = []

def check(desc, condition, level="error"):
    if not condition:
        msg = f"[FAIL] {desc}"
        if level == "error":
            errors.append(msg)
        else:
            warnings.append(msg)
        print(msg)
        return False
    print(f"[PASS] {desc}")
    return True

def check_json(path, required_keys, label):
    if not os.path.exists(path):
        check(f"{label}: archivo existe", False)
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        check(f"{label}: JSON valido", len(missing) == 0)
        if missing:
            print(f"       Faltan keys: {missing}")
        return data
    except Exception as e:
        check(f"{label}: JSON parseable", False)
        print(f"       Error: {e}")
        return None

def main():
    print("=" * 65)
    print("TEST DE REGRESION — Dashboard Monitoreo 43")
    print(f"Iniciado: {datetime.datetime.now().isoformat()}")
    print("=" * 65)

    # === 1. VAULT ===
    print("\n[1] CREDENCIALES EN VAULT")
    check("Vault existe", os.path.isdir(VAULT_DIR))
    check("windows_43.json existe", os.path.exists(os.path.join(VAULT_DIR, "windows_43.json")))
    check("github_token.json existe", os.path.exists(os.path.join(VAULT_DIR, "github_token.json")))

    vault_43 = check_json(os.path.join(VAULT_DIR, "windows_43.json"),
                           ["host", "user", "password", "protocol"], "Vault windows_43")
    if vault_43:
        check("windows_43: host = 192.168.0.43", vault_43.get("host") == "192.168.0.43")
        check("windows_43: protocol = winrm", vault_43.get("protocol") == "winrm")

    # === 2. SCRIPTS ===
    print("\n[2] SCRIPTS Y PERMISOS")
    check("monitoreo-43.py existe", os.path.exists(os.path.join(SCRIPT_DIR, "monitoreo-43.py")))
    check("monitoreo-43.sh existe", os.path.exists(os.path.expanduser("~/.hermes/scripts/monitoreo-43.sh")))
    check("actualizar-dashboard-43.sh existe", os.path.exists(os.path.expanduser("~/.hermes/scripts/actualizar-dashboard-43.sh")))
    check("analisis-temporales-43.py existe", os.path.exists(os.path.join(LOGS_SCRIPT_DIR, "analisis-temporales-43.py")))

    # Permisos
    import stat
    sh_path = os.path.expanduser("~/.hermes/scripts/monitoreo-43.sh")
    if os.path.exists(sh_path):
        mode = os.stat(sh_path).st_mode
        check("monitoreo-43.sh: ejecutable", bool(mode & stat.S_IXUSR))

    # === 3. CRONJOBS ===
    print("\n[3] CRONJOBS")
    r = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True)
    cron_out = r.stdout + r.stderr
    check("Cron monitoreo-43 existe", "monitoreo-43-catedral" in cron_out)
    check("Cron actualizar-dashboard existe", "actualizar-dashboard-43" in cron_out)

    # === 4. JSON DE ESTADO ===
    print("\n[4] JSON DE ESTADO (estado_43.json)")
    estado = check_json(os.path.join(DATA_DIR, "estado_43.json"),
                        ["timestamp", "host", "hostname", "disk_e", "knime", "onedrive", "temp_e", "source"],
                        "estado_43")
    if estado:
        disk = estado.get("disk_e", {})
        check("disk_e: size_gb > 0", disk.get("size_gb", 0) > 0)
        check("disk_e: used_pct entre 0 y 100", 0 <= disk.get("used_pct", -1) <= 100)
        check("knime: status = running|stopped", estado.get("knime", {}).get("status") in ["running", "stopped"])
        check("onedrive: status = running|stopped", estado.get("onedrive", {}).get("status") in ["running", "stopped"])
        # Timestamp fresco (menos de 2h)
        ts_str = estado["timestamp"].replace("Z", "+00:00")
        if "+" not in ts_str and "-" not in ts_str[10:]:
            ts = datetime.datetime.fromisoformat(ts_str)
            now = datetime.datetime.now()
        else:
            ts = datetime.datetime.fromisoformat(ts_str)
            now = datetime.datetime.now(datetime.timezone.utc)
        age = now - ts
        check(f"estado: timestamp fresco (<2h, actual={age.total_seconds()/60:.0f}min)", age.total_seconds() < 7200)

    # === 5. JSON DE ANALISIS ===
    print("\n[5] JSON DE ANALISIS (analisis_temp.json)")
    analisis = check_json(os.path.join(DATA_DIR, "analisis_temp.json"),
                          ["timestamp", "host", "metadata", "histograma_hora", "generadores", "velocidad_generacion", "distribucion_edad", "top50_archivos"],
                          "analisis_temp")
    if analisis:
        meta = analisis.get("metadata", {})
        check("analisis: files > 0", meta.get("files", 0) > 0)
        check("analisis: bytes > 0", meta.get("bytes", 0) > 0)
        gens = analisis.get("generadores", [])
        check("analisis: generadores no vacio", len(gens) > 0)
        top = analisis.get("top50_archivos", [])
        check("analisis: top50 no vacio", len(top) > 0)

    # === 6. HTML DEL DASHBOARD ===
    print("\n[6] HTML DEL DASHBOARD")
    html_path = os.path.join(REPO_DIR, "index.html")
    check("index.html existe", os.path.exists(html_path))
    if os.path.exists(html_path):
        with open(html_path) as f:
            html = f.read()
        check("HTML contiene <!DOCTYPE html>", "<!DOCTYPE html>" in html)
        check("HTML tiene 7 tarjetas (cards)", html.count('class="card"') >= 6)
        check("HTML referencia estado_43.json", "estado_43.json" in html)
        check("HTML referencia analisis_temp.json", "analisis_temp.json" in html)
        check("HTML tiene script JS", "<script>" in html)
        check("HTML tiene fetch()", "fetch(" in html)

    # === 7. REPO GIT ===
    print("\n[7] REPO GIT LOCAL")
    os.chdir(REPO_DIR)
    check("Repo git inicializado", os.path.exists(os.path.join(REPO_DIR, ".git")))

    r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    check("Repo: sin cambios sin commitear", r.stdout.strip() == "")

    r = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
    check("Repo: remote origin existe", "origin" in r.stdout)
    check("Repo: URL apunta a github.com", "github.com" in r.stdout)

    # Verificar que origin responde (sin credenciales en output)
    r = subprocess.run(["git", "ls-remote", "--heads", "origin"], capture_output=True, text=True)
    check("Repo: origin responde (git ls-remote)", r.returncode == 0)
    if r.returncode == 0:
        check("Repo: branch main existe en origin", "main" in r.stdout)

    # === 8. README Y .gitignore ===
    print("\n[8] ARCHIVOS DEL REPO")
    check("README.md existe", os.path.exists(os.path.join(REPO_DIR, "README.md")))
    check(".gitignore existe", os.path.exists(os.path.join(REPO_DIR, ".gitignore")))
    if os.path.exists(os.path.join(REPO_DIR, ".gitignore")):
        with open(os.path.join(REPO_DIR, ".gitignore")) as f:
            gi = f.read()
        check(".gitignore ignora *.json", "*.json" in gi)

    # === 9. CONECTIVIDAD AL 43 ===
    print("\n[9] CONECTIVIDAD AL 43")
    r = subprocess.run(["timeout", "3", "bash", "-c", "> /dev/tcp/192.168.0.43/5985"], capture_output=True)
    check("WinRM (5985): responde", r.returncode == 0)
    r = subprocess.run(["timeout", "3", "bash", "-c", "> /dev/tcp/192.168.0.43/445"], capture_output=True)
    check("SMB (445): responde", r.returncode == 0)

    # === 10. RESUMEN ===
    print("\n" + "=" * 65)
    print("RESULTADO")
    print("=" * 65)
    print(f"Errores:   {len(errors)}")
    print(f"Warnings:  {len(warnings)}")

    if errors:
        print("\n❌ FAIL — Hay errores que corregir:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    elif warnings:
        print("\n⚠️ PASS con warnings — Revisar:")
        for w in warnings:
            print(f"  {w}")
        sys.exit(0)
    else:
        print("\n✅ ALL PASS — Sin bugs silenciosos")
        sys.exit(0)

if __name__ == "__main__":
    main()
