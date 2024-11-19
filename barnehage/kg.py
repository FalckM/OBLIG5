from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY' # nødvendig for session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/barnehager')
def barnehager():
    information = select_alle_barnehager()
    return render_template('barnehager.html', data=information)

@app.route('/behandle', methods=['GET', 'POST'])
def behandle():
    if request.method == 'POST':
        sd = request.form
        soknad_obj = form_to_object_soknad(sd)  # Konverterer skjemaet til et Soknad-objekt
        tilbudt_plass = insert_soknad(soknad_obj)  # Prøver å sette inn søknaden

        # Lagre informasjon om hvorvidt plassen ble tilbudt i session
        session['information'] = sd
        session['tilbudt_plass'] = tilbudt_plass

        return redirect(url_for('svar'))

    # Hvis metoden er GET, returner skjemaet
    return render_template('soknad.html')



@app.route('/svar')
def svar():
    information = session['information']
    barnehager = select_alle_barnehager()  # Henter alle barnehagedata
    return render_template('svar.html', data=information, barnehager=barnehager)

@app.route('/commit')
def commit():
    commit_all()
    return render_template('commit.html')




"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

"""
Søkeuttrykk

"""