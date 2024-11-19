import pandas as pd
import altair as alt

#Importerer data fra nedlastet Excel ark og renser data 
kgdata = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", sheet_name="KOSandel120000",
                       header=3,
                       names=['kom','y15','y16','y17','y18','y19','y20','y21','y22','y23'],
                       na_values=['.', '..'])

for coln in ['y15','y16','y17','y18','y19','y20','y21','y22','y23']:
    mask_over_100 = (kgdata[coln] > 100)
    kgdata.loc[mask_over_100, coln] = float("nan")

kgdata.loc[724:779, 'kom'] = "NaN"
kgdata["kom"] = kgdata['kom'].str.split(" ").apply(lambda x: x[1] if len(x) > 1 else "")
kgdata_no_meta = kgdata.drop(kgdata.index[724:])

# A)

# Finner maksverdi i kolonne 23
max_value_y23 = kgdata['y23'].max()

# Lager en maske for å finne alle verdiene i kolonne 23 med høyest verdi
rows_with_max_y23 = kgdata[kgdata['y23'] == max_value_y23]

print(f"Den høyeste verdien i 'y23' er {max_value_y23} og det skjer i disse radene:")
print(rows_with_max_y23[['kom', 'y23']])

# B)

min_value_y23 = kgdata['y23'].min()

# Finner ut hva den laveste verdien i y23 er
row_with_min_y23 = kgdata[kgdata['y23'] == min_value_y23].iloc[0]

print(f"Den laveste verdien i 'y23' er {min_value_y23} og det skjer i disse radene:")
print(row_with_min_y23[['kom', 'y23']])

# C)

# Beregn gjennomsnittet for kolonnene y15 til y23 for hver kommune
kgdata['average_2015_2023'] = kgdata[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1)

# Rund av gjennomsnittene til én desimal
kgdata['average_2015_2023'] = kgdata['average_2015_2023'].round(1)

# Finn den høyeste gjennomsnittlige prosenten
max_avg = kgdata['average_2015_2023'].max()

# Finn kommuner som har dette gjennomsnittet
kommuner_med_max_avg = kgdata[kgdata['average_2015_2023'] == max_avg]

# For hver kommune med høyest gjennomsnitt, finn året med høyest prosentandel
for index, row in kommuner_med_max_avg.iterrows():
    # Finn kolonnen (året) der prosentandelen er høyest for denne kommunen
    max_year = row[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].idxmax()
    max_value = row[max_year]
    
    # Print kommunen, høyeste gjennomsnitt og hvilket år det var
    print(f"Kommune: {row['kom']}, Gjennomsnitt: {row['average_2015_2023']}%, Høyeste år: {max_year}, Høyeste prosent i år: {max_value}%")


# D)

# Beregn gjennomsnittet for kolonnene y15 til y23 for hver kommune
kgdata['average_2015_2023'] = kgdata[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1)

# Rund av gjennomsnittene til én desimal
kgdata['average_2015_2023'] = kgdata['average_2015_2023'].round(1)

# Finn den laveste gjennomsnittlige prosenten
min_avg = kgdata['average_2015_2023'].min()

# Finn kommuner som har dette gjennomsnittet
kommuner_med_min_avg = kgdata[kgdata['average_2015_2023'] == min_avg]

# For hver kommune med lavt gjennomsnitt, finn året med lavest prosentandel
for index, row in kommuner_med_min_avg.iterrows():
    # Finn kolonnen (året) der prosentandelen er lavest for denne kommunen
    min_year = row[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].idxmin()
    min_value = row[min_year]
    
    # Print kommunen, laveste gjennomsnitt og hvilket år det var
    print(f"Kommune: {row['kom']}, Gjennomsnitt: {row['average_2015_2023']}%, Laveste år: {min_year}, Laveste prosent i år: {min_value}%")

# E)

# Spesifiser hvilket år vi vil beregne gjennomsnittet for år
spesifikt_aar = 'y17'  # Bytt til 'y15', 'y16' for andre verdier

# Sjekk at det spesifiserte året er gyldig
if spesifikt_aar in ['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']:
    # Beregn gjennomsnittet for det spesifikke året, ignorer NaN-verdier
    gjennomsnitt_for_aar = kgdata[spesifikt_aar].mean()

    # Rund av gjennomsnittet til én desimal
    gjennomsnitt_for_aar = round(gjennomsnitt_for_aar, 1)

    # Print resultatet
    print(f"Den gjennomsnittlige prosenten for alle kommuner i {spesifikt_aar} er {gjennomsnitt_for_aar}%.")
else:
    print(f"Året {spesifikt_aar} er ikke gyldig. Velg et år mellom 2015 og 2023 (y15 til y23).")

# F)

# Velg kommune
valgt_kommune = "Oslo"  # Bytt til ønsket kommune

# Filtrer data for den valgte kommunen
kommune_data = kgdata[kgdata['kom'] == valgt_kommune]

# Sjekk om kommunen finnes i dataene
if kommune_data.empty:
    print(f"Kommune '{valgt_kommune}' finnes ikke i dataset.")
else:
    # Smelt data for lettere visualisering
    kommune_data_melted = kommune_data.melt(
        id_vars='kom', 
        value_vars=['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23'],
        var_name='År', 
        value_name='Prosent'
    )

    # Konverter 'År' til riktig format (2015-2023)
    kommune_data_melted['År'] = kommune_data_melted['År'].str.replace('y', '20')

    # Visualiser dataene som linjediagram
    chart = alt.Chart(kommune_data_melted).mark_line(point=True).encode(
        x=alt.X('År:N', title='År'),  # x-aksen er årene 2015-2023
        y=alt.Y('Prosent:Q', title='Prosentandel'),  # y-aksen er prosentandelen
        tooltip=['År', 'Prosent']  # Tooltip for å vise detaljer
    ).properties(
        title=f'Prosent barn i ett- og to-årsalderen i barnehagen (2015-2023) for {valgt_kommune}',
        width=800,
        height=400
    )

    # Lagre grafen som en HTML-fil
    chart.save(f'prosent_barn_{valgt_kommune}_2015_2023.html')

# G)

# Fjern rader som har NaN i noen av årene 2015-2023 for å sikre at kommunene har data for alle årene
kgdata_clean = kgdata.dropna(subset=['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']).copy()


# Beregn gjennomsnittet for kolonnene y15 til y23 for hver kommune
kgdata_clean.loc[:, 'average_2015_2023'] = kgdata_clean[['y15', 'y16', 'y17', 'y18', 'y19', 'y20', 'y21', 'y22', 'y23']].mean(axis=1)

# Rund av gjennomsnittene til én desimal
kgdata_clean.loc[:, 'average_2015_2023'] = kgdata_clean['average_2015_2023'].round(1)

# Finn de 10 kommunene med høyest gjennomsnittlig prosentandel
top_10_kommuner = kgdata_clean.nlargest(10, 'average_2015_2023')

# Visualiser resultatene med Altair
chart = alt.Chart(top_10_kommuner).mark_bar().encode(
    x=alt.X('kom:N', title='Kommune', sort='-y'),  # Kommuner på x-aksen
    y=alt.Y('average_2015_2023:Q', title='Gjennomsnittlig prosentandel (2015-2023)'),  # y-aksen for gjennomsnittsverdi
    tooltip=['kom', 'average_2015_2023']  # Tooltip for å vise detaljer
).properties(
    title='De 10 kommunene med høyest gjennomsnittlig prosentandel (2015-2023)',
    width=800,
    height=400
)

# Lagre grafen som en HTML-fil
chart.save('top_10_kommuner_2015_2023.html')


