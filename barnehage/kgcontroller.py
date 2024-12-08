# kgcontroller module
import pandas as pd
import numpy as np
from dbexcel import *
from kgmodel import *
import dbexcel as db


# CRUD metoder

# Create
# pd.append, pd.concat eller df.loc[-1] = [1,2] df.index = df.index + 1 df = df.sort_index()
def insert_foresatt(f):
    global db
    new_id = db.forelder['foresatt_id'].max() + 1 if not db.forelder.empty else 1

    # Sjekk for duplikater basert på navn og personnummer
    if not db.forelder[(db.forelder['foresatt_navn'] == f.foresatt_navn) & (db.forelder['foresatt_pnr'] == f.foresatt_pnr)].empty:
        print("Foresatt eksisterer allerede.")
        return db.forelder

    # Legg til ny foresatt
    ny_foresatt = pd.DataFrame([{
        'foresatt_id': new_id,
        'foresatt_navn': f.foresatt_navn,
        'foresatt_adresse': f.foresatt_adresse,
        'foresatt_tlfnr': f.foresatt_tlfnr,
        'foresatt_pnr': f.foresatt_pnr
    }])

    db.forelder = pd.concat([db.forelder, ny_foresatt], ignore_index=True)
    print(f"Foresatt {f.foresatt_navn} lagt til.")
    return db.forelder


def insert_barn(b):
    global db
    new_id = db.barn['barn_id'].max() + 1 if not db.barn.empty else 1

    # Sjekk for duplikater basert på personnummer
    if not db.barn[db.barn['barn_pnr'] == b.barn_pnr].empty:
        print("Barn med dette personnummeret eksisterer allerede.")
        return db.barn

    # Lag en ny rad med data
    ny_barn = pd.DataFrame([{
        'barn_id': new_id,
        'barn_pnr': b.barn_pnr
    }])

    # Oppdater den globale barn DataFrame
    db.barn = pd.concat([db.barn, ny_barn], ignore_index=True)
    print(f"Barn med personnummer {b.barn_pnr} lagt til.")
    return db.barn


def insert_soknad(s):
    global db

    # Sjekk at kolonnen 'sok_id' finnes
    if 'sok_id' not in db.soknad.columns:
        raise ValueError("Kolonnen 'sok_id' mangler i db.soknad. Sjekk Excel-filen og initialiseringen.")

    # Opprett ny søknads-ID
    new_id = db.soknad['sok_id'].max() + 1 if not db.soknad.empty else 1

    # Resten av koden for å behandle søknaden
    prioriterte_barnehager = [int(b_id) for b_id in s.barnehager_prioritert.split(',') if b_id.isdigit()]
    valgt_barnehage = None

    for b_id in prioriterte_barnehager:
        barnehage_data = db.barnehage.loc[db.barnehage['barnehage_id'] == b_id]
        if not barnehage_data.empty:
            ledige_plasser = barnehage_data.iloc[0]['barnehage_ledige_plasser']
            if s.fr_barnevern or s.fr_sykd_familie or s.fr_sykd_barn or ledige_plasser > 0:
                valgt_barnehage = b_id
                if ledige_plasser > 0:
                    db.barnehage.loc[db.barnehage['barnehage_id'] == b_id, 'barnehage_ledige_plasser'] -= 1
                break

    tilbudt_plass = valgt_barnehage is not None
    ny_soknad = pd.DataFrame([{
        'sok_id': new_id,
        'foresatt_1': s.foresatt_1.foresatt_id,
        'foresatt_2': s.foresatt_2.foresatt_id,
        'barn_1': s.barn_1.barn_id,
        'fr_barnevern': s.fr_barnevern,
        'fr_sykd_familie': s.fr_sykd_familie,
        'fr_sykd_barn': s.fr_sykd_barn,
        'fr_annet': s.fr_annet,
        'barnehager_prioritert': s.barnehager_prioritert,
        'sosken__i_barnehagen': s.sosken__i_barnehagen,
        'tidspunkt_oppstart': s.tidspunkt_oppstart,
        'brutto_inntekt': s.brutto_inntekt
    }])

    # Oppdater db.soknad og lagre til Excel
    db.soknad = pd.concat([db.soknad, ny_soknad], ignore_index=True)
    commit_all()
    return tilbudt_plass




# ---------------------------
# Read (select)

def select_alle_barnehager():
    """Returnerer en liste med alle barnehager definert i databasen dbexcel."""
    return barnehage.apply(lambda r: Barnehage(
        r['barnehage_id'],
        r['barnehage_navn'],
        r['barnehage_antall_plasser'],
        r['barnehage_ledige_plasser']
    ), axis=1).to_list()

def select_foresatt(f_navn):
    """OBS! Ignorerer duplikater"""
    series = forelder[forelder['foresatt_navn'] == f_navn]['foresatt_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0] # returnerer kun det første elementet i series

def select_barn(b_pnr):
    """OBS! Ignorerer duplikater"""
    series = barn[barn['barn_pnr'] == b_pnr]['barn_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0] # returnerer kun det første elementet i series
    
    
# --- Skriv kode for select_soknad her


# ------------------
# Update


# ------------------
# Delete


# ----- Persistent lagring ------
def commit_all():
    """Skriver alle DataFrames til Excel."""
    try:
        with pd.ExcelWriter('kgdata.xlsx', mode='w') as writer:
            db.forelder.to_excel(writer, sheet_name='foresatt', index=False)
            db.barnehage.to_excel(writer, sheet_name='barnehage', index=False)
            db.barn.to_excel(writer, sheet_name='barn', index=False)
            db.soknad.to_excel(writer, sheet_name='soknad', index=False)  # Ingen indeks
        print("Alle data lagret til Excel.")
    except Exception as e:
        print(f"Feil ved lagring til Excel: {e}")

        
# --- Diverse hjelpefunksjoner ---
def form_to_object_soknad(sd):
    """Konverterer form-data til en Soknad-instans."""
    foresatt_1 = Foresatt(0,
                          sd.get('navn_forelder_1'),
                          sd.get('adresse_forelder_1'),
                          sd.get('tlf_nr_forelder_1'),
                          sd.get('personnummer_forelder_1'))
    foresatt_2 = Foresatt(0,
                          sd.get('navn_forelder_2'),
                          sd.get('adresse_forelder_2'),
                          sd.get('tlf_nr_forelder_2'),
                          sd.get('personnummer_forelder_2'))

    # Legg til foresatte
    db.forelder = insert_foresatt(foresatt_1)
    db.forelder = insert_foresatt(foresatt_2)

    foresatt_1.foresatt_id = db.forelder.loc[db.forelder['foresatt_pnr'] == foresatt_1.foresatt_pnr, 'foresatt_id'].iloc[0]
    foresatt_2.foresatt_id = db.forelder.loc[db.forelder['foresatt_pnr'] == foresatt_2.foresatt_pnr, 'foresatt_id'].iloc[0]

    # Opprett barn og soknad
    barn_1 = Barn(0, sd.get('personnummer_barnet_1'))
    db.barn = insert_barn(barn_1)
    barn_1.barn_id = db.barn.loc[db.barn['barn_pnr'] == barn_1.barn_pnr, 'barn_id'].iloc[0]

    soknad = Soknad(0,
                    foresatt_1,
                    foresatt_2,
                    barn_1,
                    sd.get('fortrinnsrett_barnevern'),
                    sd.get('fortrinnsrett_sykdom_i_familien'),
                    sd.get('fortrinnsrett_sykdome_paa_barnet'),
                    sd.get('fortrinssrett_annet'),
                    sd.get('liste_over_barnehager_prioritert_5'),
                    sd.get('har_sosken_som_gaar_i_barnehagen'),
                    sd.get('tidspunkt_for_oppstart'),
                    sd.get('brutto_inntekt_husholdning'))
    return soknad


# Testing
def test_df_to_object_list():
    assert barnehage.apply(lambda r: Barnehage(r['barnehage_id'],
                             r['barnehage_navn'],
                             r['barnehage_antall_plasser'],
                             r['barnehage_ledige_plasser']),
         axis=1).to_list()[0].barnehage_navn == "Sunshine Preschool"