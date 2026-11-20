# =============================================================================
# ⚠️  APLICACIÓN INTENCIONALMENTE VULNERABLE — SOLO PARA DEMO
# Búnker DevSecOps Workshop
# =============================================================================
# Esta app tiene vulnerabilidades a propósito para demostrar:
#   - SQL Injection
#   - Hardcoded secrets
#   - Command injection
#   - Insecure deserialization
#   - Missing input validation
#   - Debug mode en producción
#
# 🚨 NUNCA desplegar esto en producción
# =============================================================================

import os
import pickle
import sqlite3
import subprocess

from flask import Flask, jsonify, request

app = Flask(__name__)

# ── VULN 1: Hardcoded Secret ─────────────────────────────────
# Bandit: B105 (hardcoded_password_string)
SECRET_KEY = "super_secret_key_12345"
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-ant-api03-FAKE_KEY_FOR_DEMO_ONLY"


# ── VULN 2: SQL Injection ────────────────────────────────────
# Bandit: B608 (hardcoded_sql_expressions)
@app.route("/user/<username>")
def get_user(username):
    """Vulnerable a SQL injection — el input va directo al query."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # 🚨 String formatting en SQL query = SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return jsonify({"user": result})


# ── VULN 3: Command Injection ────────────────────────────────
# Bandit: B602 (subprocess_popen_with_shell_equals_true)
@app.route("/ping")
def ping_host():
    """Vulnerable a command injection via parámetro host."""
    host = request.args.get("host", "127.0.0.1")
    # 🚨 shell=True + user input = Command Injection
    result = subprocess.run(
        f"ping -c 1 {host}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return jsonify({"output": result.stdout})


# ── VULN 4: Insecure Deserialization ─────────────────────────
# Bandit: B301 (pickle)
@app.route("/load", methods=["POST"])
def load_data():
    """Vulnerable a insecure deserialization con pickle."""
    data = request.get_data()
    # 🚨 pickle.loads de datos no confiables = RCE
    obj = pickle.loads(data)
    return jsonify({"loaded": str(obj)})


# ── VULN 5: Path Traversal ───────────────────────────────────
@app.route("/file")
def read_file():
    """Vulnerable a path traversal — sin sanitización del path."""
    filename = request.args.get("name", "readme.txt")
    # 🚨 Sin validación = se puede leer /etc/passwd
    with open(f"/app/data/{filename}") as f:
        content = f.read()
    return jsonify({"content": content})


# ── VULN 6: SSRF Potential ───────────────────────────────────
@app.route("/fetch")
def fetch_url():
    """Vulnerable a SSRF — permite hacer requests internos."""
    import urllib.request

    url = request.args.get("url", "")
    # 🚨 Sin validación de URL = SSRF a servicios internos
    response = urllib.request.urlopen(url)
    return response.read()


# ── Versión SEGURA (para comparar en el taller) ─────────────
@app.route("/user/safe/<username>")
def get_user_safe(username):
    """Versión segura con parameterized queries."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # ✅ Parameterized query — previene SQL injection
    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    )
    result = cursor.fetchone()
    conn.close()
    return jsonify({"user": result})


@app.route("/ping/safe")
def ping_host_safe():
    """Versión segura sin shell=True y con validación."""
    import re

    host = request.args.get("host", "127.0.0.1")
    # ✅ Validar que sea una IP válida
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        return jsonify({"error": "Invalid IP address"}), 400
    # ✅ Sin shell=True, argumentos como lista
    result = subprocess.run(
        ["ping", "-c", "1", host],
        capture_output=True,
        text=True,
    )
    return jsonify({"output": result.stdout})


if __name__ == "__main__":
    # ── VULN 7: Debug mode en producción ─────────────────────
    # Bandit: B201 (flask_debug_true)
    app.run(host="0.0.0.0", port=5000, debug=True)


@app.route("/calc")
def calc():
    expr = request.args.get("expr", "")
    return str(eval(expr))  # vuln nueva: code injection
