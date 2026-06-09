"""
app.py — ChemTech Calculator Toolbox
Flask-webapp voor eenvoudige berekeningen binnen de Chemische Technologie.
"""

import json
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)

from calculations import (calc_conversion, calc_density, calc_dilution,
                           calc_heat_exchanger, calc_mass_balance,
                           calc_moles, calc_neutralization,
                           calc_reactor, calc_residence_time, calc_yield)

# ---------------------------------------------------------------------------
# App-configuratie
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "chemtech-secret-2024"   # Verander dit in productie!
DATABASE = "chemtech.db"

# ---------------------------------------------------------------------------
# Database-hulpfuncties
# ---------------------------------------------------------------------------

def get_db():
    """Geef de databaseverbinding voor dit request terug."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Maak de tabellen aan als ze nog niet bestaan."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            calculator_name  TEXT NOT NULL,
            input_data       TEXT NOT NULL,
            formula          TEXT NOT NULL,
            result           TEXT NOT NULL,
            created_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()


def get_or_create_user(name):
    """Zoek een gebruiker op naam; maak hem aan als hij nog niet bestaat."""
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = db.execute("INSERT INTO users (name) VALUES (?)", (name,))
    db.commit()
    return cur.lastrowid


def save_calculation(user_id, calc_name, input_data, formula, result):
    """Sla een berekening op in de database."""
    db = get_db()
    db.execute(
        """
        INSERT INTO calculations (user_id, calculator_name, input_data, formula, result, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            calc_name,
            json.dumps(input_data, ensure_ascii=False),
            formula,
            json.dumps(result, ensure_ascii=False),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Login-decorator
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Log eerst in om de calculators te gebruiken.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Hulpfunctie: formulierwaarden veilig omzetten
# ---------------------------------------------------------------------------

def to_float(value, field_name):
    """Zet een stringwaarde om naar float; gooit ValueError met duidelijke melding."""
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"'{field_name}' moet een getal zijn.")


def to_int(value, field_name):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"'{field_name}' moet een geheel getal zijn.")


# ---------------------------------------------------------------------------
# Routes — algemeen
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username", "").strip()
        if not name:
            flash("Vul een naam in.", "danger")
            return redirect(url_for("login"))
        if len(name) > 50:
            flash("Naam mag maximaal 50 tekens bevatten.", "danger")
            return redirect(url_for("login"))

        with app.app_context():
            user_id = get_or_create_user(name)

        session["username"] = name
        session["user_id"] = user_id
        flash(f"Welkom, {name}!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Historiepagina
# ---------------------------------------------------------------------------

@app.route("/history")
@login_required
def history():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, calculator_name, input_data, formula, result, created_at
        FROM calculations
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],),
    ).fetchall()

    calculations = []
    for row in rows:
        calculations.append({
            "id": row["id"],
            "calculator_name": row["calculator_name"],
            "input_data": json.loads(row["input_data"]),
            "formula": row["formula"],
            "result": json.loads(row["result"]),
            "created_at": row["created_at"],
        })

    return render_template("history.html", calculations=calculations)


@app.route("/delete/<int:calc_id>", methods=["POST"])
@login_required
def delete_calculation(calc_id):
    db = get_db()
    # Controleer of de berekening van deze gebruiker is
    row = db.execute(
        "SELECT id FROM calculations WHERE id = ? AND user_id = ?",
        (calc_id, session["user_id"]),
    ).fetchone()

    if row is None:
        flash("Berekening niet gevonden of je hebt geen toegang.", "danger")
        return redirect(url_for("history"))

    db.execute("DELETE FROM calculations WHERE id = ?", (calc_id,))
    db.commit()
    flash("Berekening verwijderd.", "success")
    return redirect(url_for("history"))


# ---------------------------------------------------------------------------
# Calculator: Warmtewisselaar
# ---------------------------------------------------------------------------

@app.route("/calculator/heat-exchanger", methods=["GET", "POST"])
@login_required
def calc_heat_exchanger_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            process_name = request.form.get("process_name", "").strip() or "Naamloos"
            medium = request.form.get("medium", "").strip() or "Onbekend"
            mass_flow   = to_float(request.form.get("mass_flow"),   "Massastroom")
            cp          = to_float(request.form.get("cp"),          "Soortelijke warmte Cp")
            t_in        = to_float(request.form.get("t_in"),        "Begintemperatuur")
            t_out       = to_float(request.form.get("t_out"),       "Eindtemperatuur")
            hours       = to_float(request.form.get("hours"),       "Bedrijfsuren per dag")
            price       = to_float(request.form.get("price"),       "Energieprijs")

            result = calc_heat_exchanger(mass_flow, cp, t_in, t_out, hours, price)
            result["process_name"] = process_name
            result["medium"] = medium

            save_calculation(
                session["user_id"],
                "Warmtewisselaar",
                {"process_name": process_name, "medium": medium,
                 "mass_flow": mass_flow, "cp": cp,
                 "t_in": t_in, "t_out": t_out,
                 "hours": hours, "price": price},
                "Q = m · Cp · ΔT",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Warmtewisselaar energiecalculator",
        calculator="heat_exchanger",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Reactor keuzehulp
# ---------------------------------------------------------------------------

@app.route("/calculator/reactor", methods=["GET", "POST"])
@login_required
def calc_reactor_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            process_name       = request.form.get("process_name", "").strip() or "Naamloos"
            batch_or_cont      = request.form.get("batch_or_continuous", "continu")
            production_level   = request.form.get("production_level", "middel")
            mixing_needed      = request.form.get("mixing_needed", "nee")
            conversion_level   = request.form.get("conversion_level", "middel")
            volume             = to_float(request.form.get("volume"), "Reactorvolume")
            flow_rate          = to_float(request.form.get("flow_rate"), "Debiet")

            result = calc_reactor(batch_or_cont, production_level, mixing_needed,
                                  conversion_level, volume, flow_rate)
            result["process_name"] = process_name

            save_calculation(
                session["user_id"],
                "Reactor keuzehulp",
                {"process_name": process_name, "batch_or_continuous": batch_or_cont,
                 "production_level": production_level, "mixing_needed": mixing_needed,
                 "conversion_level": conversion_level, "volume": volume,
                 "flow_rate": flow_rate},
                "τ = V / Q",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Reactor keuzehulp",
        calculator="reactor",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Massabalans
# ---------------------------------------------------------------------------

@app.route("/calculator/mass-balance", methods=["GET", "POST"])
@login_required
def calc_mass_balance_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            mass_in  = to_float(request.form.get("mass_in"),  "Massa in")
            mass_out = to_float(request.form.get("mass_out"), "Massa uit")

            result = calc_mass_balance(mass_in, mass_out)
            result.update({"mass_in": mass_in, "mass_out": mass_out})

            save_calculation(
                session["user_id"], "Massabalans",
                {"mass_in": mass_in, "mass_out": mass_out},
                "Verschil = massa in − massa uit",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Massabalans calculator",
        calculator="mass_balance",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Rendement
# ---------------------------------------------------------------------------

@app.route("/calculator/yield", methods=["GET", "POST"])
@login_required
def calc_yield_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            theoretical = to_float(request.form.get("theoretical"), "Theoretische opbrengst")
            actual      = to_float(request.form.get("actual"),      "Werkelijke opbrengst")

            result = calc_yield(theoretical, actual)
            result.update({"theoretical": theoretical, "actual": actual})

            save_calculation(
                session["user_id"], "Rendement",
                {"theoretical": theoretical, "actual": actual},
                "Rendement (%) = (werkelijk / theoretisch) × 100",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Rendement calculator",
        calculator="yield_calc",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Conversie
# ---------------------------------------------------------------------------

@app.route("/calculator/conversion", methods=["GET", "POST"])
@login_required
def calc_conversion_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            initial = to_float(request.form.get("initial"), "Beginhoeveelheid")
            final   = to_float(request.form.get("final"),   "Eindhoeveelheid")

            result = calc_conversion(initial, final)
            result.update({"initial": initial, "final": final})

            save_calculation(
                session["user_id"], "Conversie",
                {"initial": initial, "final": final},
                "X (%) = (begin − eind) / begin × 100",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Conversie calculator",
        calculator="conversion",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Verblijftijd
# ---------------------------------------------------------------------------

@app.route("/calculator/residence-time", methods=["GET", "POST"])
@login_required
def calc_residence_time_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            volume    = to_float(request.form.get("volume"),    "Reactorvolume")
            flow_rate = to_float(request.form.get("flow_rate"), "Debiet")

            result = calc_residence_time(volume, flow_rate)
            result.update({"volume": volume, "flow_rate": flow_rate})

            save_calculation(
                session["user_id"], "Verblijftijd",
                {"volume": volume, "flow_rate": flow_rate},
                "τ = V / Q",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Verblijftijd calculator",
        calculator="residence_time",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Verdunning
# ---------------------------------------------------------------------------

@app.route("/calculator/dilution", methods=["GET", "POST"])
@login_required
def calc_dilution_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            c1 = to_float(request.form.get("c1"), "Beginconcentratie C1")
            v1 = to_float(request.form.get("v1"), "Beginvolume V1")
            c2 = to_float(request.form.get("c2"), "Eindconcentratie C2")

            result = calc_dilution(c1, v1, c2)
            result.update({"c1": c1, "v1": v1, "c2": c2})

            save_calculation(
                session["user_id"], "Verdunning",
                {"c1": c1, "v1": v1, "c2": c2},
                "C₁ · V₁ = C₂ · V₂",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Verdunning calculator",
        calculator="dilution",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: pH-neutralisatie
# ---------------------------------------------------------------------------

@app.route("/calculator/neutralization", methods=["GET", "POST"])
@login_required
def calc_neutralization_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            v_acid = to_float(request.form.get("v_acid"), "Volume zuur")
            c_acid = to_float(request.form.get("c_acid"), "Concentratie zuur")
            n_acid = to_int(request.form.get("n_acid"),   "Zuur-factor")
            c_base = to_float(request.form.get("c_base"), "Concentratie base")
            n_base = to_int(request.form.get("n_base"),   "Base-factor")

            result = calc_neutralization(v_acid, c_acid, n_acid, c_base, n_base)
            result.update({"v_acid": v_acid, "c_acid": c_acid,
                           "n_acid": n_acid, "c_base": c_base, "n_base": n_base})

            save_calculation(
                session["user_id"], "Neutralisatie",
                {"v_acid": v_acid, "c_acid": c_acid, "n_acid": n_acid,
                 "c_base": c_base, "n_base": n_base},
                "mol H⁺ = c_zuur · V_zuur · n_zuur",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="pH-neutralisatie calculator",
        calculator="neutralization",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Molmassa / mol
# ---------------------------------------------------------------------------

@app.route("/calculator/moles", methods=["GET", "POST"])
@login_required
def calc_moles_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            direction   = request.form.get("direction", "mass_to_mol")
            value       = to_float(request.form.get("value"),       "Invoerwaarde")
            molar_mass  = to_float(request.form.get("molar_mass"),  "Molmassa")

            result = calc_moles(direction, value, molar_mass)
            result.update({"direction": direction, "value": value, "molar_mass": molar_mass})

            formula = "n = m / M" if direction == "mass_to_mol" else "m = n · M"
            save_calculation(
                session["user_id"], "Molmassa / mol",
                {"direction": direction, "value": value, "molar_mass": molar_mass},
                formula,
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Molmassa / mol calculator",
        calculator="moles",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Calculator: Dichtheid
# ---------------------------------------------------------------------------

@app.route("/calculator/density", methods=["GET", "POST"])
@login_required
def calc_density_view():
    result = None
    error = None

    if request.method == "POST":
        try:
            mass   = to_float(request.form.get("mass"),   "Massa")
            volume = to_float(request.form.get("volume"), "Volume")

            result = calc_density(mass, volume)
            result.update({"mass": mass, "volume": volume})

            save_calculation(
                session["user_id"], "Dichtheid",
                {"mass": mass, "volume": volume},
                "ρ = m / V",
                result,
            )
            flash("Berekening opgeslagen.", "success")

        except ValueError as e:
            error = str(e)

    return render_template(
        "calculator_form.html",
        title="Dichtheid calculator",
        calculator="density",
        result=result,
        error=error,
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
