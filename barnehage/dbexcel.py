import pandas as pd

# Definer forventede kolonner
soknad_kolonner = [
    'sok_id', 'foresatt_1', 'foresatt_2', 'barn_1', 'fr_barnevern',
    'fr_sykd_familie', 'fr_sykd_barn', 'fr_annet', 'barnehager_prioritert',
    'sosken__i_barnehagen', 'tidspunkt_oppstart', 'brutto_inntekt'
]

try:
    kgdata = pd.ExcelFile('kgdata.xlsx')
    soknad = pd.read_excel(kgdata, 'soknad')
    # Sjekk at alle kolonnene finnes
    for kol in soknad_kolonner:
        if kol not in soknad.columns:
            raise ValueError(f"Kolonnen '{kol}' mangler i soknad. Initialiser Excel på nytt.")
except (FileNotFoundError, ValueError) as e:
    print(f"Feil: {e}. Initialiserer tom Excel-fil.")
    soknad = pd.DataFrame(columns=soknad_kolonner)

barnehage = pd.read_excel(kgdata, 'barnehage') if 'barnehage' in kgdata.sheet_names else pd.DataFrame()
forelder = pd.read_excel(kgdata, 'foresatt') if 'foresatt' in kgdata.sheet_names else pd.DataFrame()
barn = pd.read_excel(kgdata, 'barn') if 'barn' in kgdata.sheet_names else pd.DataFrame()
