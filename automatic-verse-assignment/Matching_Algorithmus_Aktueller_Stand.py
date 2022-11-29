import csv
from Levenshtein import distance
import pandas as pd

# Texte in Liste einzelner Verse verwandeln
def preparing_text_verse_level(text: list):
    prep_text = list(filter(None, [t.replace('\n', '') for t in text]))
    return prep_text

# Text als Liste einlesen (notwendig für Funktion 'preparing_text_verse_level')
def open_text_as_list_of_lines(path):
    with open('/Users/kiarahart/PycharmProjects/Marienleben/texte/' + path, mode='r', encoding='utf-8-sig') as f: # Pfad anpassen
        return f.readlines()

hs1 = preparing_text_verse_level(open_text_as_list_of_lines('hsb.txt'))#Name der txt-Datei mit größerer Anzahl an Versen (hsb, nibel_1)
hs2 = preparing_text_verse_level(open_text_as_list_of_lines('hsl.txt'))#Name der txt-Datei mit kleinerer Anzahl an Versen (hsl, nibel_2)

def levenshtein_distance(str1, str2):
    return (1 - distance(str1, str2)/max(len(str1), len(str2)))

def compare_verses(vers_id_hs1: int, vers_hs_1: str, hs1: list, hs2:list):
    vers_id_hs1 = int(vers_id_hs1)
    if vers_id_hs1 > len(hs2)-1:
        vers_id_hs1 = len(hs2)-1
    start_near_verses = max([0, vers_id_hs1-50])#bei hsb/hsc: 200
    end_near_verses = min([len(hs2)-1, vers_id_hs1 + 50])#bei hsb/hsc: 200
    near_verses = hs2[start_near_verses:end_near_verses]
    corresp_v = levenshtein_distance(vers_hs_1, hs2[vers_id_hs1])
    sim = [levenshtein_distance(vers_hs_1, vers) for vers in near_verses]
    if corresp_v > 0.5:
        return [hs2[vers_id_hs1], vers_id_hs1, corresp_v]
    else:
        return [hs2[sim.index(max(sim))+start_near_verses], sim.index(max(sim))+start_near_verses, max(sim)]

# csv-Datei
csv_file = open("uebersicht.csv", 'w')

with csv_file:
    # identifying header
    header = ['Vers_ID', 'Vers', 'Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Ähnlichkeitsmaß', 'Anmerkung']#, 'Duplikate']
    writer = csv.DictWriter(csv_file, fieldnames=header)
    writer.writeheader()
    # writing data row-wise into the csv file
    for vers in hs1:
        result = compare_verses(hs1.index(vers), vers, hs1, hs2)
        writer.writerow({'Vers_ID': hs1.index(vers),
                         'Vers': vers,
                         'Vorschlag_Zuordnung_Vers': result[0],
                         'Vorschlag_Zuordnung_Vers_ID': result[1],
                         'Ähnlichkeitsmaß': result[2]})

df = pd.read_csv('uebersicht.csv')

# HIER ERSTES ZWISCHENERGEBNIS

#Absteigende Sortierung der Levenshtein-Werte
# in dem dict 'df_sorted' wird in dem Format {Vers-ID: False bzw. True} für jede Vers ID festgehalten, ob es sich um einen mehrfach zugeordneten Vers handelt oder nicht.
# Als Mehrfachzuordnung zählt eine Vers-ID ab einschließlich ihrer zweiten Zuordnung.
# Durch die vorangegangene Sortierung zählt die Verszuordnung mit dem höchsten Levenshteinwert als die korrekte Zuordnung.
df_sorted = df.sort_values(by="Ähnlichkeitsmaß", ascending=False).duplicated(subset=['Vorschlag_Zuordnung_Vers_ID'], keep='first').to_dict()
duplicates = list({k: v for k, v in df_sorted.items() if v!=False}.keys())

# trage bei Doppeltzuordnungen den Wert 'n.a.' für die folgenden Tabellen-Zellen ein:
df.loc[duplicates, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Ähnlichkeitsmaß']] = "n.a."

# Suche nach identischen Versen ('Duplikaten') in Hss1
duplikate_ids = df.duplicated(subset=['Vers_ID']).to_dict()
duplikate_ids_l = list({k: v for k, v in duplikate_ids.items() if v != False}.keys())

# dict mit Hss2-Zuordnungen für die Duplikate aus Hss1
hss2_zuordnungen_duplikate = list(df['Vers_ID'][duplikate_ids_l])
duplikate_zusammengefasst = list(zip(hss2_zuordnungen_duplikate, duplikate_ids_l))

# Korrigiere die Indices der Duplikate (vormals wurde den Versen beim zweiten Auftreten die ID des erstmals auftretenden Verses verliehen)
df.loc[duplikate_ids_l, ['Vers_ID', 'Anmerkung']] = duplikate_ids_l, f'Duplikate in Zeilen {hss2_zuordnungen_duplikate}'
df.to_csv('uebersicht.csv', index=False)


#Korrektur von einzelnen Fehlversen und Andocken von fehlenden Versen vor bzw. nach einer Lücke
def correction(df):
    lst = list(df['Vorschlag_Zuordnung_Vers_ID'])
    lst_2 = list(df['Vorschlag_Zuordnung_Vers'])
    Vorschlag_Zuordnung_Vers_ID = list(pd.Series(lst,index=df['Vorschlag_Zuordnung_Vers']).items())
    for i, e in enumerate(Vorschlag_Zuordnung_Vers_ID):
        if i < len(hs2):#bei hsb / hsc: len(lst)-1
            int_before = [x for x in lst[:i] if type(x) == int] # Liste der ID's der zugeordneten Verse vor dem aktuellen Vers
            int_after = [x for x in lst[i:] if type(x) == int] # Liste der ID's der zugeordneten Verse nach dem aktuellen Vers
            if len(int_before) == 0:
                index_before = 0
            else:
                index_before = int_before[-1]
            if len(int_after) == 0:
                index_after = 1#len(hs2)
            else:
                index_after = int_after[0]
            if isinstance(e[1], str):
                # finde einzelne Fehlverse, welche die Verszählung unterbrechen
                if not(isinstance(Vorschlag_Zuordnung_Vers_ID[i+1][1], str)):
                    if not(isinstance(Vorschlag_Zuordnung_Vers_ID[i-1][1], str)):
                        if Vorschlag_Zuordnung_Vers_ID[i+1][1]-Vorschlag_Zuordnung_Vers_ID[i-1][1] == 2:
                            if Vorschlag_Zuordnung_Vers_ID[i+1][1]-1 in lst:
                                lst_2[lst.index(Vorschlag_Zuordnung_Vers_ID[i+1][1]-1)] = 'n.a.'
                                Vorschlag_Zuordnung_Vers_ID[i] = [hs2[Vorschlag_Zuordnung_Vers_ID[i+1][1]-1], Vorschlag_Zuordnung_Vers_ID[i+1][1]-1, 'Automatische Einsortierung (Kriterium: Versreihenfolge)']
                            else:
                                Vorschlag_Zuordnung_Vers_ID[i] = [hs2[Vorschlag_Zuordnung_Vers_ID[i+1][1]-1], Vorschlag_Zuordnung_Vers_ID[i+1][1]-1, 'Automatische Einsortierung (Kriterium: Versreihenfolge)']
                else:
                    if index_before % 2 != 0:
                        if hs2[index_before][-1] == hs2[index_before+1][-1]:
                            if hs2[index_before+1] in lst_2:
                                Vorschlag_Zuordnung_Vers_ID[lst_2.index(hs2[index_before+1])] = ['n.a.', 'n.a.', 'n.a.']
                                lst_2[lst_2.index(hs2[index_before+1])] = 'n.a.'
                                Vorschlag_Zuordnung_Vers_ID[lst.index(index_before)+1] = [hs2[index_before+1], index_before+1,
                                                                                          'Automatischer Anschluss an Vorvers. Kriterien: a)Versnummer des Vorverses ist ungerade  b)letzter Buchstabe des Verses stimmt mit letztem Buchstaben des Vorverses überein']

                            else:
                                Vorschlag_Zuordnung_Vers_ID[lst.index(index_before)+1] = [hs2[index_before+1], index_before+1,
                                                                                          'Automatischer Anschluss an Vorvers. Kriterien: a) Versnummer des Vorverses ist ungerade  b)letzter Buchstabe des Verses stimmt mit letztem Buchstaben des Vorverses überein']
                    elif hs2[index_after][-1] == hs2[index_after-1][-1]:
                        if hs2[index_after-1] in lst_2:
                            Vorschlag_Zuordnung_Vers_ID[lst_2.index(hs2[index_after-1])] = ['n.a.', 'n.a.', 'n.a.']
                            lst_2[lst_2.index(hs2[index_after-1])] = 'n.a.'
                            Vorschlag_Zuordnung_Vers_ID[lst.index(index_after)-1] = [hs2[index_after-1], index_after-1,
                                                                                     'Automatischer Anschluss an Nachvers. Kriterien: a) Versnummer des Vorverses ist gerade  b) letzter Buchstabe des Verses stimmt mit letztem Buchstaben des Nachverses überein']
                        else:
                            Vorschlag_Zuordnung_Vers_ID[lst.index(index_after)-1] = [hs2[index_after-1], index_after-1,
                                                                                     'Automatischer Anschluss an Nachvers. Kriterien: a) Versnummer des Vorverses ist gerade  b) letzter Buchstabe des Verses stimmt mit letztem Buchstaben des Nachverses überein']
            elif isinstance(Vorschlag_Zuordnung_Vers_ID[i-1][1], str):
                if isinstance(Vorschlag_Zuordnung_Vers_ID[i+1][1], str):
                    Vorschlag_Zuordnung_Vers_ID[i] = ['n.a.', 'n.a.', 'n.a.']

            elif isinstance(e[1], int):
                if index_after - e[1] != 1:
                    if e[1] - index_before != 1:
                        Vorschlag_Zuordnung_Vers_ID[i] = ['n.a.', 'n.a.', 'n.a.']
    return Vorschlag_Zuordnung_Vers_ID

corr_df = correction(df)# Anwenden der Funktion 'correction' auf die Daten des Dataframes

# Schreibe die in 'corr_df' gespeicherten Ergebnisse in den Dataframe
for i, k in enumerate(corr_df):
    if isinstance(k[-1], str):
        df.loc[df['Vers_ID'] == i, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung']] = k[0], k[1], k[-1]
    else:
        df.loc[df['Vers_ID'] == i, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID']] = k[0], k[1]
    if k[0] != 'n.a.':
        df.loc[df['Vers_ID'] == i, ['Ähnlichkeitsmaß']] = levenshtein_distance(hs1[i], hs2[k[1]])
    else:
        df.loc[df['Vers_ID'] == i, ['Ähnlichkeitsmaß']] = 'n.a.'
df.to_csv('uebersicht.csv', index=False)

# Entferne Einträge, die von 'n.a.'-Einträgen umschlossen sind
for index, row in df.iterrows():
    if isinstance(row['Vorschlag_Zuordnung_Vers_ID'], int):
        if df.iloc[index-1]['Vorschlag_Zuordnung_Vers_ID'] == 'n.a.':
            if df.iloc[index+1]['Vorschlag_Zuordnung_Vers_ID'] == 'n.a.':
                df.loc[df['Vers_ID'] == index, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Ähnlichkeitsmaß']] = 'n.a.'
df.to_csv('uebersicht.csv', index=False)

# Liste aller nicht zugeordneten Hss2-Verse
not_found = sorted(set(list([i for i in range(len(hs2))])).difference(list(df['Vorschlag_Zuordnung_Vers_ID'])))
# Liste der ID's aller zugeordneten Hss2-Verse (inkl. 'n.a.'-Einträge)
indices = df['Vorschlag_Zuordnung_Vers_ID'].tolist()

# Zuordnen bislang nicht zugeordneter Verse
def not_found_v(not_found, indices):
    result = {}
    for i in not_found:
        if i % 2 == 0:
            if i + 1 in indices and indices[indices.index(i+1)-1] == 'n.a.':
                result[indices.index(i+1)-1] = [hs2[i], i, 'Automatischer Anschluss an Nachvers. Kriterien: a) Versnummer ist gerade  b) Position vor Nachvers ist noch unbesetzt']
                indices[indices.index(i+1)-1] = i
        else:
            if i - 1 in indices and indices[indices.index(i-1)+1] == 'n.a.':
                result[indices.index(i-1)+1] = [hs2[i], i, 'Automatischer Anschluss an Vorvers. Kriterien: a) Versnummer ist ungerade b) Position nach Vorvers ist noch unbesetzt']
                indices[indices.index(i-1)+1] = i
    return result

result_not_v = not_found_v(not_found, indices)# Anwenden der Funktion 'not_found_v' auf die Daten des Dataframes

# Schreibe die in 'result_not_v' gespeicherten Ergebnisse in den Dataframe
for k, v in result_not_v.items():
    if isinstance(v[-1], str):
        df.loc[df['Vers_ID'] == k, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung', 'Ähnlichkeitsmaß']] = v[0], v[1], v[-1], levenshtein_distance(hs1[k],v[0])
    else:
        df.loc[df['Vers_ID'] == k, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID']] = v[0], v[1]
df.to_csv('uebersicht.csv', index=False)

# Regelt die Grenzwerte für Ls-Wert und die korrespondierende Färbung der Felder in der Excel-Tabelle
def color_rule(val):
    result = []
    for x in val:
        if x == 'n.a.':
            result.append('background-color: grey')
        elif x < 0.3:
            result.append('background-color: red')
        elif 0.3 < x < 0.6:
            result.append('background-color: orange')
        else:
            result.append('background-color: green')
    return result

# entfernt 'Überbleibsel' von Versen, die entfernt wurden (insb. Ähnlichkeitsmaß und Anmerkung)
df.loc[df['Vorschlag_Zuordnung_Vers_ID']== 'n.a.', ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Ähnlichkeitsmaß', 'Anmerkung']] = "n.a."
df.to_csv('uebersicht.csv', index=False)

# Liste aller nicht zugeordneten Hss2-Verse (aktualisierte Version von 'not_found')
not_found_2 = sorted(set(list([i for i in range(len(hs2))])).difference(list(df['Vorschlag_Zuordnung_Vers_ID'])))
# Liste der ID's aller zugeordneten Hss2-Verse (inkl. 'n.a.'-Einträge) (aktualisierte Version von 'indices')
indices_2 = df['Vorschlag_Zuordnung_Vers_ID'].tolist()

# Quelle für folgende Funktion: https://stackoverflow.com/questions/46146197/count-all-sequences-in-a-list
# Filtert Objekte in 'not_found_2' in zwei Gruppen: einzelne Fehlverse und zusammenhängende Fehlverse
# einzelne Fehlverse werden in eine gemeinsame Liste 'singles' sortiert
# zusammenhängende Fehlverse werden in eine Liste sortiert, die wiederum in die Liste 'groups' sortiert wird
def not_found_2_return_lists(not_found_2, indices_2):
    singles = []
    groups = [[]]
    for item1, item2 in zip(not_found, not_found[1:]):  # pairwise iteration
        if item2 - item1 == 1:
            if not groups[-1]:
                groups[-1].extend((item1, item2))
            else:
                groups[-1].append(item2)
        elif groups[-1]:
            groups.append([])
        else:
            singles.append(item1)
    if not groups[-1]:
        del groups[-1]
    return singles, groups

# Output der Funktion 'not_found_2_return_lists' sind die zwei Listen 'groups' und 'singles'
groups, singles = not_found_2_return_lists(not_found_2, indices_2)[1], not_found_2_return_lists(not_found, indices_2)[0]

# Füge Anmerkung bei dem Vers hinzu, nach dem der nicht zugeordnete Vers der Versreihenfolge in Hss2 folgend kommen müsste
singles_dict = {s: hs2[s] for s in singles}
for k, v in singles_dict.items():
    if k == 0:
        df.loc[df['Vers_ID'] == 0, ['Anmerkung']] = f'In Folgezeile nicht zugeordneter Vers Nr.{k} aus Hss2: {v}'
    else:
        df.loc[df['Vers_ID'] == list(df['Vorschlag_Zuordnung_Vers_ID']).index(k-1), ['Anmerkung']] = f'In Folgezeile nicht zugeordneter Vers Nr.{k} aus Hss2: {v}'

# Füge Anmerkung bei dem Vers hinzu, nach dem die nicht zugeordneten Verse der Versreihenfolge in Hss2 folgend kommen müssten
for re in groups:
    groups_dict = {x: hs2[x] for x in re}
    if re[0] == 0:
        df.loc[df['Vers_ID'] == 0, df['Anmerkung'] == 'n.a.',['Anmerkung']] = f'Zusatzverse / Nicht zugeordnete Verse: {groups_dict}'
        df.loc[df['Vers_ID'] == 0, df['Anmerkung'] != 'n.a.',['Anmerkung']] = f'{df.loc[df["Vers_ID"] == 0]}' + f'. Zusatzverse / Nicht zugeordnete Verse: {groups_dict}'
    else:
        # TODO: Aktuell werden bereits bestehende Einträge bei 'Anmerkung' überschrieben. Die beiden auskommentierten Zeilen erzeugen eine Fehlermeldung.
        df.loc[df['Vers_ID'] == list(df['Vorschlag_Zuordnung_Vers_ID']).index(re[0]-1), ['Anmerkung']] = f'Zusatzverse / Nicht zugeordnete Verse: {groups_dict}'
        #df.loc[df['Vers_ID'] == list(df['Vorschlag_Zuordnung_Vers_ID']).index(re[0]-1), df['Anmerkung'] == 'n.a.',['Anmerkung']] = f'Zusatzverse / Nicht zugeordnete Verse: {xx}'
        #df.loc[df['Vers_ID'] == list(df['Vorschlag_Zuordnung_Vers_ID']).index(re[0]-1), df['Anmerkung'] != 'n.a.',['Anmerkung']] = f'. Zusatzverse / Nicht zugeordnete Verse: {xx}'
df.to_csv('uebersicht.csv', index=False)

# Vermerke hinter Duplikaten die Position des jeweils anderen Auftretens des Verses
for i, num in enumerate(duplikate_zusammengefasst):
    df.loc[num[1], ['Vers_ID', 'Anmerkung']] = num[1], f'Identischer Vers in Hss1 in Zeile {num[0]}'
    df.loc[num[0], ['Vers_ID', 'Anmerkung']] = num[0], f'Identischer Vers in Hss1 in Zeile {num[1]}'
df.to_csv('uebersicht.csv', index=False)

# Liste der ID's aller zugeordneten Hss2-Verse (inkl. 'n.a.'-Einträge) (aktualisierte Version von 'indices' und 'indices_2')
indices_3 = df['Vorschlag_Zuordnung_Vers_ID'].tolist()

# Liste der ID's aller zugeordneten Hss2-Verse (EXKL. 'n.a.'-Einträge)
indices_found = [x for x in indices_3 if x != 'n.a.']

# Die Funktion 'get_index_disruptions' findet Stellen, an denen die Versreihenfolge von Hss2 unterbrochen wird
def get_index_disruptions(indices_found):
    if len(indices_found) == 0:
        return []
    rslt = []
    prev_val = indices_found[0]
    for val in indices_found[1:]:
        if val == prev_val:
            continue
        if val == prev_val + 1:
            prev_val = val
            continue
        rslt.append(val)
        prev_val = val
    return rslt

list_index_disruptions = get_index_disruptions(indices_found)

# Schreibe die in 'list_index_disruptions' gespeicherten Ergebnisse in den Dataframe
for index_disruption in list_index_disruptions:
    df.loc[df['Vorschlag_Zuordnung_Vers_ID'] == index_disruption, ['Anmerkung']] = 'Versreihenfolge unterbrochen'
df.to_csv('uebersicht.csv', index=False)

# entfernt 'Überbleibsel' von Versen, die entfernt wurden
df['Anmerkung'] = df['Anmerkung'].fillna('n.a.')
df.to_csv('uebersicht.csv', index=False)

# Wende die Funktion 'color_rule' auf den Dataframe an
col_df = df.style.apply(color_rule, axis=1, subset=['Ähnlichkeitsmaß'])
#col_df.to_excel(r'styled.xlsx')
