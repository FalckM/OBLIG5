from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)
import dbexcel as db
import pandas as pd
import altair as alt
import json

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY' # nødvendig for session

# Les inn data fra Excel-filen
kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", sheet_name="KOSandel120000", header=3,
                       names=['kom','y15','y16','y17','y18','y19','y20','y21','y22','y23'],
                       na_values=['.', '..'])

# Rens data (bruker koden fra Oppgave2.py)
for coln in ['y15','y16','y17','y18','y19','y20','y21','y22','y23']:
    kgdata.loc[kgdata[coln] > 100, coln] = float("nan")

kgdata.loc[724:779, 'kom'] = "NaN"
kgdata["kom"] = kgdata['kom'].str.split(" ").apply(lambda x: x[1] if len(x) > 1 else "")
kgdata_no_meta = kgdata.drop(kgdata.index[724:])

# Lag en liste over unike kommuner
unike_kommuner = kgdata_no_meta['kom'].unique()

@app.route('/statistikk', methods=['GET', 'POST'])
def statistikk():
    import altair as alt
    import pandas as pd

    # Les data fra Excel-filen
    kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", sheet_name="KOSandel120000",
                           header=3,
                           names=['kom', 'y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'],
                           na_values=['.', '..'])

    # Fjern metadata og rens dataene i kolonnen 'kom'
    kgdata["kom"] = kgdata["kom"].fillna("")  # Fyll NaN-verdier med tom streng
    kgdata["kom"] = kgdata["kom"].str.split(" ").apply(lambda x: x[1] if len(x) > 1 else "")
    kgdata_clean = kgdata.dropna(subset=['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']).copy()

    # Lag en liste over kommuner for dropdown-menyen
    kommuner = kgdata_clean["kom"].unique().tolist()

    # Håndter valgt kommune
    valgt_kommune = None
    chart_json = None
    if request.method == 'POST':
        valgt_kommune = request.form.get('kommune', None)

        if valgt_kommune:
            # Filtrer data for valgt kommune
            kommune_data = kgdata_clean[kgdata_clean['kom'] == valgt_kommune]

            if kommune_data.empty:
                return render_template('statistikk.html', kommuner=kommuner, error=f"Kommune '{valgt_kommune}' finnes ikke i dataene.")

            kommune_data_melted = kommune_data.melt(
                id_vars='kom',
                value_vars=['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'],
                var_name='År',
                value_name='Prosent'
            )
            kommune_data_melted['År'] = kommune_data_melted['År'].str.replace('y', '20')

            # Lag stolpediagram for valgt kommune
            chart = alt.Chart(kommune_data_melted).mark_bar().encode(
                x=alt.X('År:N', title='År'),
                y=alt.Y('Prosent:Q', title='Prosentandel'),
                tooltip=['År', 'Prosent']
            ).properties(
                title=f'Prosent barn i ett- og to-årsalderen i barnehagen (2015-2023) for {valgt_kommune}',
                width=800,
                height=400
            )

            # Konverter grafen til JSON
            chart_json = chart.to_json()

    # Hvis ingen kommune er valgt, vis topp-10 kommuner
    if not valgt_kommune:
        kgdata_clean['average_2015_2023'] = kgdata_clean[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1).round(1)
        top_10_kommuner = kgdata_clean.nlargest(10, 'average_2015_2023')

        # Lag stolpediagram for topp-10 kommuner
        chart = alt.Chart(top_10_kommuner).mark_bar().encode(
            x=alt.X('kom:N', title='Kommune', sort='-y'),
            y=alt.Y('average_2015_2023:Q', title='Gjennomsnittlig prosentandel (2015-2023)'),
            tooltip=['kom', 'average_2015_2023']
        ).properties(
            title='De 10 kommunene med høyest gjennomsnittlig prosentandel (2015-2023)',
            width=800,
            height=400
        )

        # Konverter grafen til JSON
        chart_json = chart.to_json()

    return render_template('statistikk.html', kommuner=kommuner, chart_json=chart_json, valgt_kommune=valgt_kommune)

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

        # Hent data om prioriterte barnehager
        prioriterte_barnehager = soknad_obj.barnehager_prioritert.split(',')
        sokte_barnehager = []
        for b_id in prioriterte_barnehager:
            barnehage_data = db.barnehage.loc[db.barnehage['barnehage_id'] == int(b_id)]
            if not barnehage_data.empty:
                sokte_barnehager.append(barnehage_data.iloc[0]['barnehage_navn'])

        # Lagre informasjon i session
        session['information'] = sd
        session['tilbudt_plass'] = tilbudt_plass

        if tilbudt_plass:
            valgt_barnehage = db.barnehage.loc[db.barnehage['barnehage_id'] == int(prioriterte_barnehager[0])]
            session['barnehage_navn'] = valgt_barnehage.iloc[0]['barnehage_navn']
            session['barnehage_adresse'] = "Ukjent Adresse"  # Oppdater dette hvis du har data
            session['barnehage_telefon'] = "123 456 789"  # Oppdater dette hvis du har data
            session['barnehage_epost'] = "kontakt@barnehage.no"  # Oppdater dette hvis du har data
        else:
            session['sokte_barnehager'] = sokte_barnehager

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

    try:
        forelder = pd.read_excel('kgdata.xlsx', sheet_name='foresatt', usecols=lambda x: 'Unnamed' not in x)
        barn = pd.read_excel('kgdata.xlsx', sheet_name='barn', usecols=lambda x: 'Unnamed' not in x)
        barnehage = pd.read_excel('kgdata.xlsx', sheet_name='barnehage', usecols=lambda x: 'Unnamed' not in x)
        soknad = pd.read_excel('kgdata.xlsx', sheet_name='soknad', usecols=lambda x: 'Unnamed' not in x)
    except Exception as e:
        return f"En feil oppstod under lasting av data fra Excel: {e}", 500

    soknader_med_data = []
    for _, row in soknad.iterrows():
        foresatt_1 = forelder.loc[forelder['foresatt_id'] == row['foresatt_1']]
        foresatt_2 = forelder.loc[forelder['foresatt_id'] == row['foresatt_2']]
        barn_data = barn.loc[barn['barn_id'] == row['barn_1']]

        har_fortrinnsrett = row['fr_barnevern'] == 'on' or row['fr_sykd_familie'] == 'on' or row['fr_sykd_barn'] == 'on'

        # Sjekk prioriterte barnehager og finn første med ledig plass
        status = "AVSLAG"
        tilbudt_barnehage = None
        prioriterte_barnehager = str(row['barnehager_prioritert']).split(',')
        for barnehage_id in prioriterte_barnehager:
            if barnehage_id.isdigit():
                barnehage_id = int(barnehage_id)
                barnehage_data = barnehage.loc[barnehage['barnehage_id'] == barnehage_id]
                if not barnehage_data.empty:
                    ledige_plasser = barnehage_data.iloc[0]['barnehage_ledige_plasser']
                    if har_fortrinnsrett or ledige_plasser > 0:
                        status = "TILBUD"
                        tilbudt_barnehage = barnehage_data.iloc[0]['barnehage_navn']
                        break

        soknader_med_data.append({
            'sok_id': row['sok_id'],
            'foresatt_1': foresatt_1['foresatt_navn'].values[0] if not foresatt_1.empty else 'Ukjent',
            'foresatt_2': foresatt_2['foresatt_navn'].values[0] if not foresatt_2.empty else 'Ukjent',
            'barn_1': barn_data['barn_pnr'].values[0] if not barn_data.empty else 'Ukjent',
            'fr_barnevern': row['fr_barnevern'],
            'fr_sykd_familie': row['fr_sykd_familie'],
            'fr_sykd_barn': row['fr_sykd_barn'],
            'fr_annet': row['fr_annet'],
            'status': status,
            'tilbudt_barnehage': tilbudt_barnehage if tilbudt_barnehage else "Ingen"
        })

    foresatt_data = forelder.to_dict(orient='records')
    barn_data = barn.to_dict(orient='records')
    barnehage_data = barnehage.to_dict(orient='records')

    return render_template('commit.html',
                           foresatt_data=foresatt_data,
                           barn_data=barn_data,
                           barnehage_data=barnehage_data,
                           soknad_data=soknader_med_data)


@app.route('/soknader')
def soknader():
    # Les oppdatert data fra Excel-filen
    try:
        forelder = pd.read_excel('kgdata.xlsx', sheet_name='foresatt', usecols=lambda x: 'Unnamed' not in x)
        barn = pd.read_excel('kgdata.xlsx', sheet_name='barn', usecols=lambda x: 'Unnamed' not in x)
        barnehage = pd.read_excel('kgdata.xlsx', sheet_name='barnehage', usecols=lambda x: 'Unnamed' not in x)
        soknad = pd.read_excel('kgdata.xlsx', sheet_name='soknad', usecols=lambda x: 'Unnamed' not in x)
    except Exception as e:
        return f"En feil oppstod under lasting av data fra Excel: {e}", 500

    soknader_med_data = []
    for _, row in soknad.iterrows():
        foresatt_1 = forelder.loc[forelder['foresatt_id'] == row['foresatt_1']]
        foresatt_2 = forelder.loc[forelder['foresatt_id'] == row['foresatt_2']]
        barn_data = barn.loc[barn['barn_id'] == row['barn_1']]

        har_fortrinnsrett = row['fr_barnevern'] == 'on' or row['fr_sykd_familie'] == 'on' or row['fr_sykd_barn'] == 'on'

        # Sjekk prioriterte barnehager og finn første med ledig plass
        status = "AVSLAG"
        tilbudt_barnehage = None
        prioriterte_barnehager = str(row['barnehager_prioritert']).split(',')
        for barnehage_id in prioriterte_barnehager:
            if barnehage_id.isdigit():
                barnehage_id = int(barnehage_id)
                barnehage_data = barnehage.loc[barnehage['barnehage_id'] == barnehage_id]
                if not barnehage_data.empty:
                    ledige_plasser = barnehage_data.iloc[0]['barnehage_ledige_plasser']
                    if har_fortrinnsrett or ledige_plasser > 0:
                        status = "TILBUD"
                        tilbudt_barnehage = barnehage_data.iloc[0]['barnehage_navn']
                        break

        soknader_med_data.append({
            'sok_id': row['sok_id'],
            'foresatt_1': foresatt_1['foresatt_navn'].values[0] if not foresatt_1.empty else 'Ukjent',
            'foresatt_2': foresatt_2['foresatt_navn'].values[0] if not foresatt_2.empty else 'Ukjent',
            'barn_1': barn_data['barn_pnr'].values[0] if not barn_data.empty else 'Ukjent',
            'fr_barnevern': row['fr_barnevern'],
            'fr_sykd_familie': row['fr_sykd_familie'],
            'fr_sykd_barn': row['fr_sykd_barn'],
            'fr_annet': row['fr_annet'],
            'status': status,
            'tilbudt_barnehage': tilbudt_barnehage if tilbudt_barnehage else "Ingen"
        })

    return render_template('soknader.html', soknader=soknader_med_data)


"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

"""
Søkeuttrykk

"""