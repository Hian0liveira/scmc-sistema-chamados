from datetime import datetime
import os
from pathlib import Path
import secrets
import sqlite3
import re
from functools import wraps
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "scmc.db"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SCMC_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL DEFAULT '',
  job_title TEXT NOT NULL DEFAULT '',
  sector TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL DEFAULT '',
  extension TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL CHECK(role IN ('Administrador','Técnico','Solicitante')),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS equipment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_tag TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  brand TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  serial TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'Ativo' CHECK(status IN ('Ativo','Em manutenção','Inativo')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS service_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  number TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'Média' CHECK(priority IN ('Baixa','Média','Alta','Crítica')),
  status TEXT NOT NULL DEFAULT 'Aberta' CHECK(status IN ('Aberta','Em atendimento','Aguardando','Concluída','Cancelada')),
  opened_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  closed_at TEXT,
  solution TEXT NOT NULL DEFAULT '',
  requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  technician_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
  equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  actor_name TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  details TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ticket_responses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES service_orders(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  actor_name TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  response TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS catalog_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  value TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(kind,value)
);
CREATE TABLE IF NOT EXISTS appearance_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL DEFAULT ''
);
"""

CATALOGS = {
    "types": ("Tipos de equipamento", "equipment", "category"),
    "brands": ("Marcas", "equipment", "brand"),
    "models": ("Modelos", "equipment", "model"),
    "sectors": ("Setores", "users", "sector"),
}
DEFAULT_APPEARANCE = {
    "primary": "#4263eb", "accent": "#31d4e4", "background": "#f5f7fb",
    "sidebar": "#101b2b", "sidebar_text": "#d5deea", "surface": "#ffffff",
    "text": "#172638", "muted": "#718096", "border": "#e7edf4",
    "success": "#11936f", "warning": "#d99618", "danger": "#d64545",
    "logo": "", "banner": "",
}

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    columns = {row[1] for row in db.execute("PRAGMA table_info(users)")}
    migrations = {
        "password_hash": "TEXT NOT NULL DEFAULT ''",
        "job_title": "TEXT NOT NULL DEFAULT ''",
        "sector": "TEXT NOT NULL DEFAULT ''",
        "phone": "TEXT NOT NULL DEFAULT ''",
        "extension": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in migrations.items():
        if name not in columns:
            db.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
    schema = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()[0]
    if "Administrador" not in schema:
        db.commit()
        db.execute("PRAGMA foreign_keys=OFF")
        db.executescript("""
        BEGIN IMMEDIATE;
        CREATE TABLE users_new (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL DEFAULT '',
          job_title TEXT NOT NULL DEFAULT '',
          sector TEXT NOT NULL DEFAULT '',
          phone TEXT NOT NULL DEFAULT '',
          extension TEXT NOT NULL DEFAULT '',
          role TEXT NOT NULL CHECK(role IN ('Administrador','Técnico','Solicitante')),
          active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO users_new(id,name,email,password_hash,job_title,sector,phone,extension,role,active,created_at)
          SELECT id,name,email,password_hash,job_title,sector,phone,extension,role,active,created_at FROM users;
        DROP TABLE users;
        ALTER TABLE users_new RENAME TO users;
        COMMIT;
        """)
        db.execute("PRAGMA foreign_keys=ON")
    if db.execute("SELECT COUNT(*) FROM users WHERE role='Administrador' AND active=1").fetchone()[0] == 0:
        db.execute("UPDATE users SET role='Administrador' WHERE id=(SELECT id FROM users WHERE active=1 AND password_hash!='' ORDER BY created_at,id LIMIT 1)")
    equipment_columns = {row[1] for row in db.execute("PRAGMA table_info(equipment)")}
    for name in ("serial", "description"):
        if name not in equipment_columns:
            db.execute(f"ALTER TABLE equipment ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
    for kind, (_, table, column) in CATALOGS.items():
        for row in db.execute(f"SELECT DISTINCT {column} FROM {table} WHERE trim({column})!=''"):
            db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES(?,?)", (kind, row[0]))
    for row in db.execute("SELECT DISTINCT location FROM equipment WHERE trim(location)!=''"):
        db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES('sectors',?)", (row[0],))
    for key, value in DEFAULT_APPEARANCE.items():
        db.execute("INSERT OR IGNORE INTO appearance_settings(key,value) VALUES(?,?)", (key, value))
    db.commit()
    db.close()

init_db()

def setup_required():
    row = get_db().execute("SELECT COUNT(*) FROM users WHERE password_hash!=''").fetchone()
    return row[0] == 0

def technician_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None or g.user["role"] not in ("Técnico", "Administrador"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None or g.user["role"] != "Administrador":
            abort(403)
        return view(*args, **kwargs)
    return wrapped

@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = get_db().execute("SELECT * FROM users WHERE id=? AND active=1", (user_id,)).fetchone() if user_id else None
    if user_id and g.user is None:
        session.clear()

    public_endpoints = {"login", "logout", "setup", "register", "static"}
    if request.endpoint in public_endpoints:
        if request.endpoint == "setup" and not setup_required():
            return redirect(url_for("login"))
        if request.endpoint == "register" and setup_required():
            return redirect(url_for("setup"))
        return None

    if g.user is None:
        return redirect(url_for("setup" if setup_required() else "login"))

@app.context_processor
def inject_current_user():
    appearance = dict(DEFAULT_APPEARANCE)
    if g.user:
        appearance.update(dict(get_db().execute("SELECT key,value FROM appearance_settings")))
    return {"current_user": g.user, "appearance": appearance}

def password_pair_valid(password, confirmation):
    if len(password) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if password != confirmation:
        raise ValueError("As senhas não coincidem.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("index"))
    if setup_required():
        return redirect(url_for("setup"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE lower(email)=? AND active=1", (email,)).fetchone()
        if user and user["password_hash"] and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        flash("E-mail ou senha inválidos.", "error")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("login"))

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if not setup_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            v = form_required("name", "email", "job_title", "sector", "phone", "extension")
            password = request.form.get("password", "")
            password_pair_valid(password, request.form.get("confirm_password", ""))
            db = get_db()
            email = v["email"].lower()
            db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES('sectors',?)", (v["sector"],))
            existing = db.execute("SELECT id FROM users WHERE lower(email)=?", (email,)).fetchone()
            if existing:
                db.execute("UPDATE users SET name=?,password_hash=?,job_title=?,sector=?,phone=?,extension=?,role='Administrador',active=1 WHERE id=?",
                           (v["name"], generate_password_hash(password), v["job_title"], v["sector"], v["phone"], v["extension"], existing["id"]))
            else:
                db.execute("INSERT INTO users(name,email,password_hash,job_title,sector,phone,extension,role) VALUES(?,?,?,?,?,?,?,'Administrador')",
                           (v["name"], email, generate_password_hash(password), v["job_title"], v["sector"], v["phone"], v["extension"]))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE lower(email)=?", (email,)).fetchone()
            log_activity("Configuração inicial de Administrador", "Pessoa", user["id"], "Conta inicial criada", actor=user)
            session.clear()
            session["user_id"] = user["id"]
            flash("Conta inicial de Administrador criada. Agora você pode gerenciar todos os perfis.", "success")
            return redirect(url_for("index"))
        except (ValueError, sqlite3.IntegrityError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "Esse e-mail já está cadastrado.", "error")
    return render_template("setup.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if setup_required():
        return redirect(url_for("setup"))
    if g.user:
        return redirect(url_for("index"))
    if request.method == "POST":
        try:
            v = form_required("name", "email", "job_title", "sector", "phone", "extension")
            password = request.form.get("password", "")
            password_pair_valid(password, request.form.get("confirm_password", ""))
            db = get_db()
            db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES('sectors',?)", (v["sector"],))
            db.execute("INSERT INTO users(name,email,password_hash,job_title,sector,phone,extension,role) VALUES(?,?,?,?,?,?,?,'Solicitante')",
                       (v["name"], v["email"].lower(), generate_password_hash(password), v["job_title"], v["sector"], v["phone"], v["extension"]))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE lower(email)=?", (v["email"].lower(),)).fetchone()
            log_activity("Auto cadastro de solicitante", "Pessoa", user["id"], f"Setor: {v['sector']} · Função: {v['job_title']}", actor=user)
            session.clear()
            session["user_id"] = user["id"]
            flash("Conta criada. Seu nome será usado automaticamente nos chamados.", "success")
            return redirect(url_for("index"))
        except (ValueError, sqlite3.IntegrityError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "Esse e-mail já está cadastrado.", "error")
    return render_template("register.html")

def get_or_404(table, item_id):
    row = get_db().execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
    if row is None:
        abort(404)
    return row

def form_required(*names):
    values = {name: request.form.get(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ValueError("Preencha todos os campos obrigatórios.")
    return values

def log_activity(action, entity, entity_id, details="", actor=None):
    actor = actor or g.user
    if not actor:
        return
    get_db().execute(
        "INSERT INTO activity_log(actor_id,actor_name,actor_role,action,entity,entity_id,details) VALUES(?,?,?,?,?,?,?)",
        (actor["id"], actor["name"], actor["role"], action, entity, str(entity_id), details),
    )
    get_db().commit()

def run_write(sql, params, success, endpoint, **kwargs):
    try:
        db = get_db()
        db.execute(sql, params)
        db.commit()
        flash(success, "success")
    except (sqlite3.IntegrityError, ValueError) as exc:
        flash(str(exc) if isinstance(exc, ValueError) else "Não foi possível salvar: confira e-mail, patrimônio e vínculos.", "error")
        return False
    return True

@app.route("/")
def index():
    db = get_db()
    requester_filter = " AND requester_id=?" if g.user["role"] == "Solicitante" else ""
    query_args = (g.user["id"],) if requester_filter else ()
    stats = {
        "open": db.execute("SELECT COUNT(*) FROM service_orders WHERE status NOT IN ('Concluída','Cancelada')" + requester_filter, query_args).fetchone()[0],
        "equipment": db.execute("SELECT COUNT(*) FROM equipment WHERE status!='Inativo'").fetchone()[0],
        "users": db.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0] if g.user["role"] != "Solicitante" else 1,
    }
    latest = db.execute("""SELECT o.*, e.asset_tag, u.name requester FROM service_orders o
      JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      WHERE o.status NOT IN ('Concluída','Cancelada')""" + requester_filter + " ORDER BY o.id DESC LIMIT 6", query_args).fetchall()
    activity = db.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 8").fetchall() if g.user["role"] == "Administrador" else []
    return render_template("index.html", stats=stats, latest=latest, activity=activity)

@app.get("/activity")
@admin_required
def activity_log_view():
    q = request.args.get("q", "").strip()
    rows = get_db().execute("SELECT * FROM activity_log WHERE actor_name LIKE ? OR action LIKE ? OR entity LIKE ? OR details LIKE ? ORDER BY id DESC LIMIT 250", tuple([f"%{q}%"]*4)).fetchall()
    return render_template("activity.html", rows=rows, q=q)

@app.get("/admin")
@admin_required
def admin():
    db = get_db()
    catalogs = {}
    for kind, (label, _, _) in CATALOGS.items():
        catalogs[kind] = {"label": label, "rows": db.execute(
            "SELECT * FROM catalog_items WHERE kind=? ORDER BY value COLLATE NOCASE", (kind,)
        ).fetchall()}
    return render_template("admin.html", catalogs=catalogs)

def catalog_label(kind):
    if kind not in CATALOGS:
        abort(404)
    return CATALOGS[kind]

@app.post("/admin/catalog/<kind>/create")
@admin_required
def catalog_create(kind):
    label, _, _ = catalog_label(kind)
    value = request.form.get("value", "").strip()
    if not value:
        flash("Informe o nome do cadastro.", "error")
    else:
        try:
            db = get_db()
            cur = db.execute("INSERT INTO catalog_items(kind,value) VALUES(?,?)", (kind, value))
            db.commit()
            log_activity("Cadastro de opção", label, cur.lastrowid, value)
            flash(f"Opção adicionada em {label}.", "success")
        except sqlite3.IntegrityError:
            flash("Essa opção já existe no cadastro.", "error")
    return redirect(url_for("admin"))

@app.post("/admin/catalog/<kind>/<int:item_id>/edit")
@admin_required
def catalog_edit(kind, item_id):
    label, table, column = catalog_label(kind)
    value = request.form.get("value", "").strip()
    if not value:
        flash("Informe o nome do cadastro.", "error")
        return redirect(url_for("admin"))
    db = get_db()
    old = db.execute("SELECT value FROM catalog_items WHERE id=? AND kind=?", (item_id, kind)).fetchone()
    if old is None:
        abort(404)
    try:
        db.execute("UPDATE catalog_items SET value=? WHERE id=? AND kind=?", (value, item_id, kind))
        db.execute(f"UPDATE {table} SET {column}=? WHERE {column}=?", (value, old["value"]))
        if kind == "sectors":
            db.execute("UPDATE equipment SET location=? WHERE location=?", (value, old["value"]))
        db.commit()
        log_activity("Edição de opção", label, item_id, f"{old['value']} → {value}")
        flash("Cadastro atualizado; os registros vinculados também foram atualizados.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Essa opção já existe no cadastro.", "error")
    return redirect(url_for("admin"))

@app.post("/admin/catalog/<kind>/<int:item_id>/delete")
@admin_required
def catalog_delete(kind, item_id):
    label, table, column = catalog_label(kind)
    db = get_db()
    row = db.execute("SELECT value FROM catalog_items WHERE id=? AND kind=?", (item_id, kind)).fetchone()
    if row is None:
        abort(404)
    usage = db.execute(f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (row["value"],)).fetchone()[0]
    if kind == "sectors":
        usage += db.execute("SELECT COUNT(*) FROM equipment WHERE location=?", (row["value"],)).fetchone()[0]
    if usage:
        flash(f"Não é possível excluir: {usage} cadastro(s) ainda usam essa opção. Edite os registros ou altere o valor primeiro.", "error")
    else:
        db.execute("DELETE FROM catalog_items WHERE id=? AND kind=?", (item_id, kind))
        db.commit()
        log_activity("Exclusão de opção", label, item_id, row["value"])
        flash("Opção excluída.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/appearance")
@admin_required
def appearance_save():
    db = get_db()
    try:
        values = {}
        for key in DEFAULT_APPEARANCE:
            if key in ("logo", "banner"):
                continue
            value = request.form.get(key, DEFAULT_APPEARANCE[key]).strip()
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError("Escolha cores válidas para todos os campos.")
            values[key] = value
        upload_dir = BASE_DIR / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        for key in ("logo", "banner"):
            uploaded = request.files.get(key)
            if uploaded and uploaded.filename:
                ext = Path(secure_filename(uploaded.filename)).suffix.lower()
                allowed = {".png", ".jpg", ".jpeg", ".webp"}
                if ext not in allowed:
                    raise ValueError("Use imagens PNG, JPG ou WebP para o logo e o banner.")
                filename = f"{key}-{secrets.token_hex(10)}{ext}"
                uploaded.save(upload_dir / filename)
                values[key] = filename
            elif request.form.get(f"remove_{key}") == "1":
                values[key] = ""
            else:
                values[key] = dict(db.execute("SELECT key,value FROM appearance_settings")).get(key, "")
        db.executemany("INSERT INTO appearance_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", values.items())
        db.commit()
        log_activity("Atualização da aparência", "Sistema", "Cyrex", "Cores, logotipo ou banner atualizados")
        flash("Aparência salva.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin"))

@app.post("/admin/appearance/reset-colors")
@admin_required
def appearance_reset_colors():
    db = get_db()
    colors = {key: value for key, value in DEFAULT_APPEARANCE.items() if key not in ("logo", "banner")}
    db.executemany("INSERT INTO appearance_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", colors.items())
    db.commit()
    log_activity("Restauração das cores padrão", "Sistema", "Cyrex", "Paleta de cores padrão restaurada; logo e banner preservados")
    flash("Cores padrão restauradas. Logotipo e banner foram mantidos.", "success")
    return redirect(url_for("admin"))

@app.route("/users")
@admin_required
def users():
    q = request.args.get("q", "").strip()
    rows = get_db().execute("SELECT * FROM users WHERE name LIKE ? OR email LIKE ? OR sector LIKE ? OR role LIKE ? ORDER BY active DESC, name", tuple([f"%{q}%"]*4)).fetchall()
    return render_template("users.html", rows=rows, q=q)

@app.route("/users/new", methods=["GET","POST"])
@admin_required
def user_new():
    if request.method == "POST":
        try:
            v=form_required("name","email","job_title","sector","phone","extension","role")
            if v["role"] not in ("Administrador","Técnico","Solicitante"): raise ValueError("Perfil inválido.")
            password=request.form.get("password", "")
            password_pair_valid(password, request.form.get("confirm_password", ""))
            db=get_db(); db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES('sectors',?)",(v["sector"],)); cur=db.execute("INSERT INTO users(name,email,password_hash,job_title,sector,phone,extension,role) VALUES(?,?,?,?,?,?,?,?)",(v["name"],v["email"].lower(),generate_password_hash(password),v["job_title"],v["sector"],v["phone"],v["extension"],v["role"]))
            db.commit(); log_activity("Cadastro de pessoa", "Pessoa", cur.lastrowid, f"Perfil: {v['role']} · Setor: {v['sector']}"); flash("Usuário cadastrado.","success"); return redirect(url_for("users"))
        except (ValueError, sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Esse e-mail já está cadastrado.","error")
    return render_template("user_form.html", row=None)

@app.route("/users/<int:item_id>/edit", methods=["GET","POST"])
@admin_required
def user_edit(item_id):
    row=get_or_404("users",item_id)
    if request.method=="POST":
        try:
            v=form_required("name","email","job_title","sector","phone","extension","role")
            if v["role"] not in ("Administrador","Técnico","Solicitante"): raise ValueError("Perfil inválido.")
            if item_id == g.user["id"] and (v["role"] != "Administrador" or request.form.get("active") != "1"):
                raise ValueError("Não é possível desativar ou rebaixar a própria conta administradora.")
            target=get_db().execute("SELECT role,active FROM users WHERE id=?",(item_id,)).fetchone()
            if target and target["role"]=="Administrador" and target["active"] and v["role"]!="Administrador" and get_db().execute("SELECT COUNT(*) FROM users WHERE role='Administrador' AND active=1").fetchone()[0]<=1:
                raise ValueError("Mantenha pelo menos um administrador ativo.")
            db=get_db(); password=request.form.get("password", "")
            db.execute("INSERT OR IGNORE INTO catalog_items(kind,value) VALUES('sectors',?)",(v["sector"],))
            if password:
                password_pair_valid(password, request.form.get("confirm_password", ""))
                db.execute("UPDATE users SET name=?,email=?,job_title=?,sector=?,phone=?,extension=?,role=?,active=?,password_hash=? WHERE id=?",(v["name"],v["email"].lower(),v["job_title"],v["sector"],v["phone"],v["extension"],v["role"],int(request.form.get("active")=="1"),generate_password_hash(password),item_id))
            else:
                db.execute("UPDATE users SET name=?,email=?,job_title=?,sector=?,phone=?,extension=?,role=?,active=? WHERE id=?",(v["name"],v["email"].lower(),v["job_title"],v["sector"],v["phone"],v["extension"],v["role"],int(request.form.get("active")=="1"),item_id))
            db.commit()
            log_activity("Edição de pessoa", "Pessoa", item_id, f"Perfil: {v['role']} · Setor: {v['sector']}")
            flash("Usuário atualizado.","success"); return redirect(url_for("users"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "E-mail já utilizado.","error")
        row=get_or_404("users",item_id)
    return render_template("user_form.html",row=row)

@app.post("/users/<int:item_id>/delete")
@admin_required
def user_delete(item_id):
    if item_id == g.user["id"]:
        flash("Você não pode excluir sua própria conta enquanto está conectado.", "error")
        return redirect(url_for("users"))
    try:
        db=get_db()
        target=db.execute("SELECT role,active FROM users WHERE id=?",(item_id,)).fetchone()
        if target and target["role"]=="Administrador" and target["active"] and db.execute("SELECT COUNT(*) FROM users WHERE role='Administrador' AND active=1").fetchone()[0]<=1:
            flash("Mantenha pelo menos um administrador ativo.","error")
            return redirect(url_for("users"))
        db.execute("UPDATE users SET active=0 WHERE id=?",(item_id,)); db.commit(); log_activity("Inativação de pessoa", "Pessoa", item_id, "Conta inativada; chamados preservados"); flash("Usuário inativado. O histórico dos chamados foi preservado.","success")
    except sqlite3.IntegrityError: flash("Não foi possível inativar o usuário.","error")
    return redirect(url_for("users"))

@app.route("/equipment")
def equipment():
    q=request.args.get("q", "").strip()
    query="SELECT * FROM equipment WHERE (asset_tag LIKE ? OR category LIKE ? OR brand LIKE ? OR model LIKE ? OR location LIKE ? OR serial LIKE ?)"
    args=[f"%{q}%"]*6
    if g.user["role"] == "Solicitante": query += " AND status!='Inativo'"
    query += " ORDER BY id DESC"
    rows=get_db().execute(query,args).fetchall()
    return render_template("equipment.html",rows=rows,q=q)

def equipment_catalogs():
    db = get_db()
    return {kind: db.execute("SELECT value FROM catalog_items WHERE kind=? ORDER BY value COLLATE NOCASE", (kind,)).fetchall()
            for kind in ("types", "brands", "models", "sectors")}

def validate_equipment_catalogs(values):
    db = get_db()
    for field, kind in (("category", "types"), ("brand", "brands"), ("model", "models"), ("location", "sectors")):
        if not db.execute("SELECT 1 FROM catalog_items WHERE kind=? AND value=?", (kind, values[field])).fetchone():
            raise ValueError("Selecione tipo, marca, modelo e setor cadastrados no painel Admin.")

@app.route("/equipment/new",methods=["GET","POST"])
@admin_required
def equipment_new():
    if request.method=="POST":
        try:
            v=form_required("asset_tag","category","brand","model","location")
            validate_equipment_catalogs(v)
            v["serial"]=request.form.get("serial","").strip()
            v["description"]=request.form.get("description","").strip()
            db=get_db(); cur=db.execute("INSERT INTO equipment(asset_tag,category,brand,model,location,serial,description) VALUES(?,?,?,?,?,?,?)",tuple(v.values())); db.commit(); log_activity("Cadastro de equipamento", "Equipamento", cur.lastrowid, f"Patrimônio: {v['asset_tag']} · Setor: {v['location']}")
            flash("Equipamento cadastrado.","success"); return redirect(url_for("equipment"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Patrimônio já cadastrado.","error")
    return render_template("equipment_form.html",row=None,catalogs=equipment_catalogs())

@app.route("/equipment/<int:item_id>/edit",methods=["GET","POST"])
@admin_required
def equipment_edit(item_id):
    row=get_or_404("equipment",item_id)
    if request.method=="POST":
        try:
            v=form_required("asset_tag","category","brand","model","location")
            validate_equipment_catalogs(v)
            v["serial"]=request.form.get("serial","").strip()
            v["description"]=request.form.get("description","").strip()
            status=request.form.get("status","Ativo")
            if status not in ("Ativo","Em manutenção","Inativo"): raise ValueError("Status inválido.")
            db=get_db(); db.execute("UPDATE equipment SET asset_tag=?,category=?,brand=?,model=?,location=?,serial=?,description=?,status=? WHERE id=?",(*v.values(),status,item_id)); db.commit(); log_activity("Edição de equipamento", "Equipamento", item_id, f"Patrimônio: {v['asset_tag']} · Status: {status}")
            flash("Equipamento atualizado.","success"); return redirect(url_for("equipment"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Patrimônio já cadastrado.","error")
        row=get_or_404("equipment",item_id)
    return render_template("equipment_form.html",row=row,catalogs=equipment_catalogs())

@app.post("/equipment/<int:item_id>/delete")
@admin_required
def equipment_delete(item_id):
    try:
        db=get_db(); db.execute("DELETE FROM equipment WHERE id=?",(item_id,)); db.commit(); log_activity("Exclusão de equipamento", "Equipamento", item_id, "Equipamento excluído do inventário"); flash("Equipamento excluído.","success")
    except sqlite3.IntegrityError: flash("Equipamento possui ordens vinculadas. Edite e marque como Inativo.","error")
    return redirect(url_for("equipment"))

@app.route("/orders")
def orders():
    db=get_db(); q=request.args.get("q","").strip(); status=request.args.get("status","")
    sql="""SELECT o.*,e.asset_tag,u.name requester, t.name technician FROM service_orders o
      JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      LEFT JOIN users t ON t.id=o.technician_id WHERE 1=1"""
    args=[]
    if g.user["role"] == "Solicitante":
        sql += " AND o.requester_id=?"
        args.append(g.user["id"])
    if q: sql+=" AND (o.number LIKE ? OR o.title LIKE ? OR e.asset_tag LIKE ?)"; args += [f"%{q}%"]*3
    if status: sql+=" AND o.status=?"; args.append(status)
    sql+=" ORDER BY o.id DESC"
    rows=db.execute(sql,args).fetchall()
    return render_template("orders.html",rows=rows,q=q,status=status,statuses=["Aberta","Em atendimento","Aguardando","Concluída","Cancelada"])

def order_form_data():
    db=get_db(); people=db.execute("SELECT id,name,role,sector FROM users WHERE active=1 ORDER BY name").fetchall()
    equipment_query="SELECT id,asset_tag,category,brand,model,location FROM equipment WHERE status!='Inativo'"
    if g.user["role"] == "Solicitante":
        equipment_query += " AND lower(trim(location))=lower(trim(?))"
        equipment_rows=db.execute(equipment_query+" ORDER BY asset_tag",(g.user["sector"],)).fetchall()
    else:
        equipment_rows=db.execute(equipment_query+" ORDER BY asset_tag").fetchall()
    return people,equipment_rows

@app.route("/orders/new",methods=["GET","POST"])
def order_new():
    if g.user["role"] == "Técnico":
        abort(403)
    db=get_db(); people,equipment_rows=order_form_data(); technicians=[u for u in people if u["role"] == "Técnico"]
    if request.method=="POST":
        try:
            v=form_required("title","description","priority","equipment_id")
            selected_equipment=db.execute("SELECT id,location,status FROM equipment WHERE id=?",(int(v["equipment_id"]),)).fetchone()
            if not selected_equipment or selected_equipment["status"]=="Inativo":
                raise ValueError("Selecione um equipamento ativo.")
            if g.user["role"] == "Solicitante" and selected_equipment["location"].strip().casefold()!=g.user["sector"].strip().casefold():
                raise ValueError("O equipamento precisa pertencer ao seu setor.")
            number="OS-"+datetime.now().strftime("%y%m%d%H%M%S%f")
            now=datetime.now().isoformat(timespec="minutes")
            selected=db.execute("SELECT location,status FROM equipment WHERE id=?",(int(v["equipment_id"]),)).fetchone()
            if not selected or selected["status"]=="Inativo": raise ValueError("Selecione um equipamento ativo.")
            if g.user["role"]=="Solicitante" and selected["location"].strip().casefold()!=g.user["sector"].strip().casefold(): raise ValueError("O equipamento precisa pertencer ao seu setor.")
            cur=db.execute("INSERT INTO service_orders(number,title,description,priority,status,opened_at,updated_at,requester_id,equipment_id) VALUES(?,?,?,?,?,?,?,?,?)",(number,v["title"],v["description"],v["priority"],"Aberta",now,now,g.user["id"],int(v["equipment_id"])))
            db.commit(); log_activity("Abertura de chamado", "Chamado", cur.lastrowid, f"{number} · {v['title']}"); flash(f"Ordem {number} aberta.","success"); return redirect(url_for("orders"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Confira solicitante, equipamento e prioridade.","error")
    return render_template("order_form.html",row=None,technicians=technicians,equipment_rows=equipment_rows)

@app.route("/orders/<int:item_id>")
def order_detail(item_id):
    db=get_db()
    row=db.execute("""SELECT o.*,e.asset_tag,e.category,e.brand,e.model,e.location,e.serial,e.description equipment_description,u.name requester,u.email requester_email,t.name technician
      FROM service_orders o JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      LEFT JOIN users t ON t.id=o.technician_id WHERE o.id=?""",(item_id,)).fetchone()
    if row is None: abort(404)
    if g.user["role"] == "Solicitante" and row["requester_id"] != g.user["id"]:
        abort(403)
    history=db.execute("SELECT * FROM activity_log WHERE entity='Chamado' AND entity_id=? ORDER BY id DESC",(str(item_id),)).fetchall()
    responses=db.execute("SELECT * FROM ticket_responses WHERE order_id=? ORDER BY id DESC",(item_id,)).fetchall()
    return render_template("order_detail.html",row=row,history=history,responses=responses)

@app.post("/orders/<int:item_id>/responses")
@technician_required
def order_response(item_id):
    get_or_404("service_orders",item_id)
    try:
        response=form_required("response")["response"]
        db=get_db(); db.execute("INSERT INTO ticket_responses(order_id,user_id,actor_name,actor_role,response) VALUES(?,?,?,?,?)",(item_id,g.user["id"],g.user["name"],g.user["role"],response)); db.commit()
        log_activity("Resposta ao chamado", "Chamado", item_id, response)
        flash("Resposta registrada no chamado.","success")
    except ValueError as exc:
        flash(str(exc),"error")
    return redirect(url_for("order_detail",item_id=item_id))

@app.route("/orders/<int:item_id>/edit",methods=["GET","POST"])
@technician_required
def order_edit(item_id):
    row=get_or_404("service_orders",item_id); db=get_db(); people,equipment_rows=order_form_data(); technicians=[u for u in people if u["role"] == "Técnico"]
    if request.method=="POST":
        try:
            v=form_required("title","description","priority","status","requester_id","equipment_id")
            technician=request.form.get("technician_id") or None
            if v["status"] not in ("Aberta","Em atendimento","Aguardando","Concluída","Cancelada"): raise ValueError("Status inválido.")
            closed=datetime.now().isoformat(timespec="minutes") if v["status"]=="Concluída" else None
            solution=request.form.get("solution","").strip()
            if v["status"]=="Concluída" and not solution: raise ValueError("Informe a solução antes de concluir.")
            old_values={"status":row["status"],"priority":row["priority"],"title":row["title"]}
            db.execute("UPDATE service_orders SET title=?,description=?,priority=?,status=?,updated_at=?,closed_at=?,solution=?,requester_id=?,technician_id=?,equipment_id=? WHERE id=?",(v["title"],v["description"],v["priority"],v["status"],datetime.now().isoformat(timespec="minutes"),closed,solution,int(v["requester_id"]),int(technician) if technician else None,int(v["equipment_id"]),item_id))
            db.commit(); changes=[]
            for field,label in (("status","status"),("priority","prioridade"),("title","assunto")):
                if old_values[field]!=v["title" if field=="title" else field]: changes.append(f"{label}: {old_values[field]} → {v['title' if field=='title' else field]}")
            log_activity("Atualização de chamado", "Chamado", item_id, "; ".join(changes) or "Dados do atendimento atualizados")
            flash("Ordem atualizada.","success"); return redirect(url_for("order_detail",item_id=item_id))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Confira os vínculos informados.","error")
        row=get_or_404("service_orders",item_id)
    return render_template("order_form.html",row=row,people=people,technicians=technicians,equipment_rows=equipment_rows)

@app.post("/orders/<int:item_id>/delete")
@technician_required
def order_delete(item_id):
    db=get_db(); db.execute("DELETE FROM service_orders WHERE id=?",(item_id,)); db.commit(); log_activity("Exclusão de chamado", "Chamado", item_id, "Chamado excluído"); flash("Ordem excluída.","success"); return redirect(url_for("orders"))

@app.route("/orders/<int:item_id>/close",methods=["GET","POST"])
@technician_required
def order_close(item_id):
    row=get_or_404("service_orders",item_id)
    if request.method=="POST":
        solution=request.form.get("solution","").strip()
        if not solution: flash("Descreva a solução para concluir a ordem.","error")
        else:
            now=datetime.now().isoformat(timespec="minutes"); db=get_db(); db.execute("UPDATE service_orders SET status='Concluída',solution=?,closed_at=?,updated_at=? WHERE id=?",(solution,now,now,item_id)); db.commit(); log_activity("Conclusão de chamado", "Chamado", item_id, "Status alterado para Concluída; solução registrada"); flash("Ordem concluída.","success"); return redirect(url_for("order_detail",item_id=item_id))
    return render_template("close_order.html",row=row)

@app.cli.command("init-db")
def init_db_command():
    init_db(); print(f"Banco criado em {DATABASE}")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
