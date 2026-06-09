# ChemTech Calculator Toolbox

Een Flask-webapp met eenvoudige berekeningen voor studenten Chemische Technologie.

## Calculators

| # | Calculator | Formule |
|---|-----------|---------|
| 1 | Warmtewisselaar energiecalculator | Q = m · Cp · ΔT |
| 2 | Reactor keuzehulp | τ = V / Q |
| 3 | Massabalans | Δm = massa in − massa uit |
| 4 | Rendement | η = (werkelijk / theoretisch) × 100% |
| 5 | Conversie | X = (begin − eind) / begin × 100% |
| 6 | Verblijftijd | τ = V / Q |
| 7 | Verdunning | C₁ · V₁ = C₂ · V₂ |
| 8 | pH-neutralisatie | mol H⁺ = c · V · n |
| 9 | Molmassa / mol | n = m / M |
| 10 | Dichtheid | ρ = m / V |

## Lokaal opstarten

```bash
# 1. Maak een virtuele omgeving aan
python3 -m venv venv

# 2. Activeer de omgeving
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# 3. Installeer de afhankelijkheden
pip install -r requirements.txt

# 4. Start de app
python app.py
```

Open vervolgens je browser op: **http://127.0.0.1:5000**

## Tests uitvoeren

```bash
pytest tests/
```

## Projectstructuur

```
chemtech/
├── app.py                  ← Flask-app (routes + helpers)
├── calculations.py         ← Alle berekenfuncties
├── requirements.txt        ← Python-afhankelijkheden
├── Procfile                ← Voor Render/Gunicorn
├── README.md
├── templates/
│   ├── base.html           ← Basistemplate (navbar, footer)
│   ├── home.html           ← Homepage met kaartenraster
│   ├── login.html          ← Inlogpagina
│   ├── history.html        ← Historieoverzicht
│   └── calculator_form.html← Universeel calculatorformulier
├── static/
│   └── style.css           ← Alle stijlen
└── tests/
    └── test_calculations.py← Unit tests
```

## Deployen op Render

1. Push je project naar GitHub.
2. Maak een nieuw **Web Service** aan op [render.com](https://render.com).
3. Koppel je repository.
4. Render detecteert automatisch de `Procfile` en gebruikt `gunicorn app:app`.
5. Zorg dat de **Build Command** `pip install -r requirements.txt` is.
6. De app draait standaard op poort 10000; Render regelt dit automatisch.

> **Let op:** De SQLite-database wordt aangemaakt in dezelfde map als `app.py`.
> Op Render wordt de database gereset bij elke deploy. Gebruik voor productie
> een persistente database zoals PostgreSQL (via de Render add-on).

## Technische keuzes

- **Flask** als microframework — eenvoudig en goed gedocumenteerd.
- **SQLite** als database — geen extra installatie nodig, ideaal voor studie.
- **Jinja2 templates** — HTML-rendering via Flask ingebouwde templating.
- **Sessies** — Flask-sessies voor eenvoudig login (alleen naam, geen wachtwoord).
- **calculations.py** — berekeningen los van de routes, gemakkelijk te testen.
