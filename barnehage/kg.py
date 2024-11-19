from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)
from dbexcel import soknad, barnehage, barn, forelder
import pandas as pd
import altair as alt
import json

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY' # nødvendig for session

# Les inn data fra Excel-filen
kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", sheet_name="KOSandel120000", header=3,
                       names=['kom','y15','y16','y17','y18','y19','y20','y21','y22','y23'],
                       na_values=['.', '..'])

# Rens data (bruker koden du har fra Oppgave2.py)
for coln in ['y15','y16','y17','y18','y19','y20','y21','y22','y23']:
    kgdata.loc[kgdata[coln] > 100, coln] = float("nan")

kgdata.loc[724:779, 'kom'] = "NaN"
kgdata["kom"] = kgdata['kom'].str.split(" ").apply(lambda x: x[1] if len(x) > 1 else "")
kgdata_no_meta = kgdata.drop(kgdata.index[724:])

# Lag en liste over unike kommuner
unike_kommuner = kgdata_no_meta['kom'].unique()

@app.route('/statistikk', methods=['GET', 'POST'])
def statistikk():
    valgt_kommune = None
    chart_html = None

    if request.method == 'POST':
        valgt_kommune = request.form['kommune']
        kommune_data = kgdata_no_meta[kgdata_no_meta['kom'] == valgt_kommune]

        if not kommune_data.empty:
            kommune_data_melted = kommune_data.melt(
                id_vars='kom',
                value_vars=['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'],
                var_name='År',
                value_name='Prosent'
            )
            kommune_data_melted['År'] = kommune_data_melted['År'].str.replace('y', '20')

            chart = alt.Chart(kommune_data_melted).mark_line(point=True).encode(
                x=alt.X('År:N', title='År'),
                y=alt.Y('Prosent:Q', title='Prosentandel'),
                tooltip=['År', 'Prosent']
            ).properties(
                title=f'Prosent barn i ett- og to-årsalderen i barnehagen (2015-2023) for {valgt_kommune}',
                width=800,
                height=400
            )

            # Konverter grafen til JSON for Altair
            chart_html = json.dumps(chart.to_dict())

    return render_template('statistikk.html', kommuner=unike_kommuner, valgt_kommune=valgt_kommune, chart_html=chart_html)


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
    # Henter all data fra databasen (kgdata.xlsx) som er lastet inn i DataFrames
    foresatt_data = forelder.to_dict(orient='records')
    barn_data = barn.to_dict(orient='records')
    barnehage_data = barnehage.to_dict(orient='records')  # Konverterer barnehage DataFrame til dict

    # Henter søknader og kobler navn, personnummer, fortrinnsrett og status
    soknader_med_info = []
    for s in soknad.to_dict(orient='records'):
        # Hent navnene til foresatte
        foresatt_1_info = forelder.loc[forelder['foresatt_id'] == s['foresatt_1']]
        foresatt_1_navn = foresatt_1_info.iloc[0]['foresatt_navn'] if not foresatt_1_info.empty else "Ukjent"

        foresatt_2_info = forelder.loc[forelder['foresatt_id'] == s['foresatt_2']]
        foresatt_2_navn = foresatt_2_info.iloc[0]['foresatt_navn'] if not foresatt_2_info.empty else "Ukjent"

        # Hent personnummeret til barnet
        barn_info = barn.loc[barn['barn_id'] == s['barn_1']]
        barn_pnr = barn_info.iloc[0]['barn_pnr'] if not barn_info.empty else "Ukjent"

        # Sjekk fortrinnsrett
        har_fortrinnsrett = s['fr_barnevern'] == 'on' or s['fr_sykd_familie'] == 'on' or s['fr_sykd_barn'] == 'on'

        # Bestem status (TILBUD eller AVSLAG)
        status = "AVSLAG"
        barnehager_prioritert = str(s['barnehager_prioritert'])
        prioriterte_barnehager = [int(b_id) for b_id in barnehager_prioritert.split(',') if b_id.isdigit()]

        # Sjekk om noen av de prioriterte barnehagene har ledige plasser eller fortrinnsrett
        for b_id in prioriterte_barnehager:
            barnehage_data_row = barnehage.loc[barnehage['barnehage_id'] == b_id]
            if not barnehage_data_row.empty:
                ledige_plasser = barnehage_data_row.iloc[0]['barnehage_ledige_plasser']
                if har_fortrinnsrett or ledige_plasser > 0:
                    status = "TILBUD"
                    break

        soknader_med_info.append({
            'sok_id': s['sok_id'],
            'foresatt_1_navn': foresatt_1_navn,
            'foresatt_2_navn': foresatt_2_navn,
            'barn_pnr': barn_pnr,
            'fortrinnsrett': "Ja" if har_fortrinnsrett else "Nei",
            'status': status
        })

    return render_template('commit.html', 
                           foresatt_data=foresatt_data,
                           barn_data=barn_data,
                           barnehage_data=barnehage_data,
                           soknad_data=soknader_med_info)

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