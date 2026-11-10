from datetime import datetime
import os
from pathlib import Path
import sqlite3
from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "scmc.db"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SCMC_SECRET_KEY", "chave-local-apenas-para-desenvolvimento")

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK(role IN ('Técnico','Solicitante')),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS equipment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_tag TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  brand TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
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
"""

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
    db.commit()
    db.close()

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
    stats = {
        "open": db.execute("SELECT COUNT(*) FROM service_orders WHERE status NOT IN ('Concluída','Cancelada')").fetchone()[0],
        "equipment": db.execute("SELECT COUNT(*) FROM equipment WHERE status!='Inativo'").fetchone()[0],
        "users": db.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0],
    }
    latest = db.execute("""SELECT o.*, e.asset_tag, u.name requester FROM service_orders o
      JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      ORDER BY o.id DESC LIMIT 6""").fetchall()
    return render_template("index.html", stats=stats, latest=latest)

@app.route("/users")
def users():
    rows = get_db().execute("SELECT * FROM users ORDER BY active DESC, name").fetchall()
    return render_template("users.html", rows=rows)

@app.route("/users/new", methods=["GET","POST"])
def user_new():
    if request.method == "POST":
        try:
            v=form_required("name","email","role")
            if v["role"] not in ("Técnico","Solicitante"): raise ValueError("Perfil inválido.")
            get_db().execute("INSERT INTO users(name,email,role) VALUES(?,?,?)",(v["name"],v["email"],v["role"]))
            get_db().commit(); flash("Usuário cadastrado.","success"); return redirect(url_for("users"))
        except (ValueError, sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Esse e-mail já está cadastrado.","error")
    return render_template("user_form.html", row=None)

@app.route("/users/<int:item_id>/edit", methods=["GET","POST"])
def user_edit(item_id):
    row=get_or_404("users",item_id)
    if request.method=="POST":
        try:
            v=form_required("name","email","role")
            if v["role"] not in ("Técnico","Solicitante"): raise ValueError("Perfil inválido.")
            db=get_db(); db.execute("UPDATE users SET name=?,email=?,role=?,active=? WHERE id=?",(v["name"],v["email"],v["role"],int(request.form.get("active")=="1"),item_id)); db.commit()
            flash("Usuário atualizado.","success"); return redirect(url_for("users"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "E-mail já utilizado.","error")
        row=get_or_404("users",item_id)
    return render_template("user_form.html",row=row)

@app.post("/users/<int:item_id>/delete")
def user_delete(item_id):
    try:
        db=get_db(); db.execute("DELETE FROM users WHERE id=?",(item_id,)); db.commit(); flash("Usuário excluído.","success")
    except sqlite3.IntegrityError: flash("Usuário relacionado a ordens. Edite e inative o cadastro.","error")
    return redirect(url_for("users"))

@app.route("/equipment")
def equipment():
    rows=get_db().execute("SELECT * FROM equipment ORDER BY id DESC").fetchall()
    return render_template("equipment.html",rows=rows)

@app.route("/equipment/new",methods=["GET","POST"])
def equipment_new():
    if request.method=="POST":
        try:
            v=form_required("asset_tag","category","brand","model","location")
            get_db().execute("INSERT INTO equipment(asset_tag,category,brand,model,location) VALUES(?,?,?,?,?)",tuple(v.values())); get_db().commit()
            flash("Equipamento cadastrado.","success"); return redirect(url_for("equipment"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Patrimônio já cadastrado.","error")
    return render_template("equipment_form.html",row=None)

@app.route("/equipment/<int:item_id>/edit",methods=["GET","POST"])
def equipment_edit(item_id):
    row=get_or_404("equipment",item_id)
    if request.method=="POST":
        try:
            v=form_required("asset_tag","category","brand","model","location")
            status=request.form.get("status","Ativo")
            if status not in ("Ativo","Em manutenção","Inativo"): raise ValueError("Status inválido.")
            db=get_db(); db.execute("UPDATE equipment SET asset_tag=?,category=?,brand=?,model=?,location=?,status=? WHERE id=?",(*v.values(),status,item_id)); db.commit()
            flash("Equipamento atualizado.","success"); return redirect(url_for("equipment"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Patrimônio já cadastrado.","error")
        row=get_or_404("equipment",item_id)
    return render_template("equipment_form.html",row=row)

@app.post("/equipment/<int:item_id>/delete")
def equipment_delete(item_id):
    try:
        db=get_db(); db.execute("DELETE FROM equipment WHERE id=?",(item_id,)); db.commit(); flash("Equipamento excluído.","success")
    except sqlite3.IntegrityError: flash("Equipamento possui ordens vinculadas. Edite e marque como Inativo.","error")
    return redirect(url_for("equipment"))

@app.route("/orders")
def orders():
    db=get_db(); q=request.args.get("q","").strip(); status=request.args.get("status","")
    sql="""SELECT o.*,e.asset_tag,u.name requester, t.name technician FROM service_orders o
      JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      LEFT JOIN users t ON t.id=o.technician_id WHERE 1=1"""
    args=[]
    if q: sql+=" AND (o.number LIKE ? OR o.title LIKE ? OR e.asset_tag LIKE ?)"; args += [f"%{q}%"]*3
    if status: sql+=" AND o.status=?"; args.append(status)
    sql+=" ORDER BY o.id DESC"
    rows=db.execute(sql,args).fetchall()
    return render_template("orders.html",rows=rows,q=q,status=status,statuses=["Aberta","Em atendimento","Aguardando","Concluída","Cancelada"])

def order_form_data():
    db=get_db(); people=db.execute("SELECT id,name,role FROM users WHERE active=1 ORDER BY name").fetchall(); equipment_rows=db.execute("SELECT id,asset_tag,category,brand,model FROM equipment WHERE status!='Inativo' ORDER BY asset_tag").fetchall()
    return people,equipment_rows

@app.route("/orders/new",methods=["GET","POST"])
def order_new():
    db=get_db(); people,equipment_rows=order_form_data()
    if request.method=="POST":
        try:
            v=form_required("title","description","priority","requester_id","equipment_id")
            number="OS-"+datetime.now().strftime("%y%m%d%H%M%S%f")
            now=datetime.now().isoformat(timespec="minutes")
            db.execute("INSERT INTO service_orders(number,title,description,priority,status,opened_at,updated_at,requester_id,equipment_id) VALUES(?,?,?,?,?,?,?,?,?)",(number,v["title"],v["description"],v["priority"],"Aberta",now,now,int(v["requester_id"]),int(v["equipment_id"])))
            db.commit(); flash(f"Ordem {number} aberta.","success"); return redirect(url_for("orders"))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Confira solicitante, equipamento e prioridade.","error")
    return render_template("order_form.html",row=None,people=people,equipment_rows=equipment_rows)

@app.route("/orders/<int:item_id>")
def order_detail(item_id):
    row=get_db().execute("""SELECT o.*,e.asset_tag,e.category,e.brand,e.model,e.location,u.name requester,u.email requester_email,t.name technician
      FROM service_orders o JOIN equipment e ON e.id=o.equipment_id JOIN users u ON u.id=o.requester_id
      LEFT JOIN users t ON t.id=o.technician_id WHERE o.id=?""",(item_id,)).fetchone()
    if row is None: abort(404)
    return render_template("order_detail.html",row=row)

@app.route("/orders/<int:item_id>/edit",methods=["GET","POST"])
def order_edit(item_id):
    row=get_or_404("service_orders",item_id); db=get_db(); people,equipment_rows=order_form_data()
    if request.method=="POST":
        try:
            v=form_required("title","description","priority","status","requester_id","equipment_id")
            technician=request.form.get("technician_id") or None
            if v["status"] not in ("Aberta","Em atendimento","Aguardando","Concluída","Cancelada"): raise ValueError("Status inválido.")
            closed=datetime.now().isoformat(timespec="minutes") if v["status"]=="Concluída" else None
            solution=request.form.get("solution","").strip()
            if v["status"]=="Concluída" and not solution: raise ValueError("Informe a solução antes de concluir.")
            db.execute("UPDATE service_orders SET title=?,description=?,priority=?,status=?,updated_at=?,closed_at=?,solution=?,requester_id=?,technician_id=?,equipment_id=? WHERE id=?",(v["title"],v["description"],v["priority"],v["status"],datetime.now().isoformat(timespec="minutes"),closed,solution,int(v["requester_id"]),int(technician) if technician else None,int(v["equipment_id"]),item_id))
            db.commit(); flash("Ordem atualizada.","success"); return redirect(url_for("order_detail",item_id=item_id))
        except (ValueError,sqlite3.IntegrityError) as e: flash(str(e) if isinstance(e,ValueError) else "Confira os vínculos informados.","error")
        row=get_or_404("service_orders",item_id)
    return render_template("order_form.html",row=row,people=people,equipment_rows=equipment_rows)

@app.post("/orders/<int:item_id>/delete")
def order_delete(item_id):
    db=get_db(); db.execute("DELETE FROM service_orders WHERE id=?",(item_id,)); db.commit(); flash("Ordem excluída.","success"); return redirect(url_for("orders"))

@app.route("/orders/<int:item_id>/close",methods=["GET","POST"])
def order_close(item_id):
    row=get_or_404("service_orders",item_id)
    if request.method=="POST":
        solution=request.form.get("solution","").strip()
        if not solution: flash("Descreva a solução para concluir a ordem.","error")
        else:
            now=datetime.now().isoformat(timespec="minutes"); db=get_db(); db.execute("UPDATE service_orders SET status='Concluída',solution=?,closed_at=?,updated_at=? WHERE id=?",(solution,now,now,item_id)); db.commit(); flash("Ordem concluída.","success"); return redirect(url_for("order_detail",item_id=item_id))
    return render_template("close_order.html",row=row)

@app.cli.command("init-db")
def init_db_command():
    init_db(); print(f"Banco criado em {DATABASE}")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
