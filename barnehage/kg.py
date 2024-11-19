from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)
from dbexcel import soknad, barnehage, barn, forelder

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


@app.route('/soknader')
def soknader():
    # Henter alle søknader fra databasen
    alle_soknader = soknad.to_dict(orient='records')

    # Opprett en liste med søknader og deres status
    soknader_med_status = []
    for s in alle_soknader:
        status = "AVSLAG"  # Start med status som AVSLAG
        # Sørg for at barnehager_prioritert er en streng før split
        barnehager_prioritert = str(s['barnehager_prioritert'])

        # Del opp barnehager_prioritert og filtrer bare gyldige tall
        prioriterte_barnehager = [int(b_id) for b_id in barnehager_prioritert.split(',') if b_id.isdigit()]

        # Sjekk om søkeren har fortrinnsrett
        har_fortrinnsrett = s['fr_barnevern'] == 'on' or s['fr_sykd_familie'] == 'on' or s['fr_sykd_barn'] == 'on'

        # Sjekk om noen av de prioriterte barnehagene har ledige plasser
        for b_id in prioriterte_barnehager:
            barnehage_data = barnehage.loc[barnehage['barnehage_id'] == b_id]
            if not barnehage_data.empty:
                ledige_plasser = barnehage_data.iloc[0]['barnehage_ledige_plasser']
                # Status settes til "TILBUD" bare hvis det er ledige plasser eller fortrinnsrett
                if har_fortrinnsrett or ledige_plasser > 0:
                    status = "TILBUD"
                    break  # Bryt ut av løkken hvis vi finner en gyldig barnehage

        # Hent navnene til foresatte
        foresatt_1_info = forelder.loc[forelder['foresatt_id'] == s['foresatt_1']]
        foresatt_1_navn = foresatt_1_info.iloc[0]['foresatt_navn'] if not foresatt_1_info.empty else "Ukjent"

        foresatt_2_info = forelder.loc[forelder['foresatt_id'] == s['foresatt_2']]
        foresatt_2_navn = foresatt_2_info.iloc[0]['foresatt_navn'] if not foresatt_2_info.empty else "Ukjent"

        # Hent mer informasjon om barnet
        barn_info = barn.loc[barn['barn_id'] == s['barn_1']]
        barn_pnr = barn_info.iloc[0]['barn_pnr'] if not barn_info.empty else "Ukjent"

        soknader_med_status.append({
            'sok_id': s['sok_id'],
            'foresatt_1': foresatt_1_navn,
            'foresatt_2': foresatt_2_navn,
            'barn_1': barn_pnr,
            'status': status
        })

    return render_template('soknader.html', soknader=soknader_med_status)
"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

"""
Søkeuttrykk

"""