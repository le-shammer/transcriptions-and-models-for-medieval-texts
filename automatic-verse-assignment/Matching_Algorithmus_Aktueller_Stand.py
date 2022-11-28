import csv
#from scipy.spatial import distance
#from nltk Import edit_distance
from Levenshtein import distance
from Levenshtein import ratio
import pandas as pd


# Texte in Liste einzelner Verse verwandeln
def preparing_text_verse_level(text: list):
    prep_text = list(filter(None, [t.replace('\n', '') for t in text]))
    return prep_text

# Text als Liste einlesen (notwendig für Funktion 'preparing_text_verse_level')
def open_text_as_list_of_lines(path):
    with open('/Users/kiarahart/PycharmProjects/Marienleben/texte/' + path, mode='r', encoding='utf-8-sig') as f:
        return f.readlines()

hs1 = preparing_text_verse_level(open_text_as_list_of_lines())#Name der txt-Datei mit größerer Anzahl an Versen
hs2 = preparing_text_verse_level(open_text_as_list_of_lines())#Name der txt-Datei mit kleinerer Anzahl an Versen


def levenshtein_distance(str1, str2):
    return (1 - distance(str1, str2)/max(len(str1), len(str2)))

def compare_verses(vers_id_hs1: int, vers_hs_1: str, hs1: list, hs2:list):
    vers_id_hs1 = int(vers_id_hs1)

    if vers_id_hs1 > len(hs2)-1:
        vers_id_hs1 = len(hs2)-1

    start_near_verses = max([0, vers_id_hs1-50])
    #if vers_id_hs1 <= 50:#50:#bei hsb/hsc: 200
    #    start_near_verses = 0
    #else:
    #    start_near_verses = vers_id_hs1 - 50#50#bei hsb/hsc: 200

    end_near_verses = min([len(hs2)-1, vers_id_hs1 + 50])
    #if vers_id_hs1 > len(hs1)-1: # Denkfehler?

    #    end_near_verses = len(hs1)-1
    #else:
    #    end_near_verses = int(vers_id_hs1 + 50)#bei hsb/hsc: 200

    near_verses = hs2[start_near_verses:end_near_verses]
    corresp_v = levenshtein_distance(vers_hs_1, hs2[vers_id_hs1])
    sim = [levenshtein_distance(vers_hs_1, vers) for vers in near_verses]
    #sim2 = [levenshtein_distance(vers_hs_1, vers) for vers in hs2]
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
df = df.sort_values(by="Ähnlichkeitsmaß", ascending=False)
# in dem dict 'state_duplicated' wird in dem Format {Vers-ID: False bzw. True} für jede Vers ID festgehalten, ob es sich um ein Duplikat handelt oder nicht.
# Als Duplikat zählt eine Vers-ID ab ab einschließlich ihrem zweiten Auftreten.
# Durch die vorangegangene Sortierung zählt die Verszuordnung mit dem höchsten Levenshteinwert als das Original (bzw. 'Nicht-Duplikat').
state_duplicated = df.duplicated(subset=['Vorschlag_Zuordnung_Vers_ID']).to_dict()

# Anschließend werden die Duplikate herausgefiltert und in einer eigenen Liste 'duplicates'
duplicates = list({k: v for k, v in state_duplicated.items() if v != False}.keys())


# Abschließend wird der df wieder in die ursprüngliche Reihenfolge gebracht (Orientierung an Versreihenfolge von hs1)
df = df.sort_values(by="Vers_ID").drop_duplicates()
#TODO: vgl. Zeilen 2929 und 1376
for i in duplicates:
    df.loc[df['Vers_ID']== i, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Ähnlichkeitsmaß']] = "n.a."
df.to_csv('uebersicht.csv', index=False)

def correction(df):
    lst = list(df['Vorschlag_Zuordnung_Vers_ID'])
    lst_2 = list(df['Vorschlag_Zuordnung_Vers'])
    Vorschlag_Zuordnung_Vers_ID = list(pd.Series(lst,index=df['Vorschlag_Zuordnung_Vers']).items())
    for i, e in enumerate(Vorschlag_Zuordnung_Vers_ID):
        if i < len(hs2):#hs2): #bei hsb / hsc: len(lst)-1
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
                                Vorschlag_Zuordnung_Vers_ID[i] = [hs2[Vorschlag_Zuordnung_Vers_ID[i+1][1]-1], Vorschlag_Zuordnung_Vers_ID[i+1][1]-1, '* Einzelner Fehlvers']
                            else:
                                Vorschlag_Zuordnung_Vers_ID[i] = [hs2[Vorschlag_Zuordnung_Vers_ID[i+1][1]-1], Vorschlag_Zuordnung_Vers_ID[i+1][1]-1, '* Einzelner Fehlvers']
                else:
                    if index_before+1 % 2 != 0:
                        if hs2[index_before][-1] == hs2[index_before+1][-1]:#hs1[i][-1]
                            if hs2[index_before+1] in lst_2:
                                Vorschlag_Zuordnung_Vers_ID[lst_2.index(hs2[index_before+1])] = ['n.a.', 'n.a.', 'n.a.']
                                lst_2[lst_2.index(hs2[index_before+1])] = 'n.a.'
                                Vorschlag_Zuordnung_Vers_ID[lst.index(index_before)+1] = [hs2[index_before+1], index_before+1, '* Endung vor.V.']
                            else:
                                Vorschlag_Zuordnung_Vers_ID[lst.index(index_before)+1] = [hs2[index_before+1], index_before+1, '* Endung vor.V.']

                    elif hs2[index_after][-1] == hs2[index_after-1][-1]:#hs1[i][-1]
                        if hs2[index_after-1] in lst_2:
                            Vorschlag_Zuordnung_Vers_ID[lst_2.index(hs2[index_after-1])] = ['n.a.', 'n.a.', 'n.a.']
                            lst_2[lst_2.index(hs2[index_after-1])] = 'n.a.'
                            Vorschlag_Zuordnung_Vers_ID[lst.index(index_after)-1] = [hs2[index_after-1], index_after-1, '* Endung nachf.V.']
                        else:
                            Vorschlag_Zuordnung_Vers_ID[lst.index(index_after)-1] = [hs2[index_after-1], index_after-1, '* Endung nachf.V.']

            elif isinstance(Vorschlag_Zuordnung_Vers_ID[i-1][1], str):
                if isinstance(Vorschlag_Zuordnung_Vers_ID[i+1][1], str):
                    Vorschlag_Zuordnung_Vers_ID[i] = ['n.a.', 'n.a.', 'n.a.']

    return Vorschlag_Zuordnung_Vers_ID


corr_df = correction(df)# Dataframe

for i, k in enumerate(corr_df):
    if isinstance(k[-1], str):
        df.loc[df['Vers_ID'] == i, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung']] = k[0], k[1], k[-1]
    else:
        df.loc[df['Vers_ID'] == i, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung']] = k[0], k[1], 'n.a.'
    if k[0] != 'n.a.':
        df.loc[df['Vers_ID'] == i, ['Ähnlichkeitsmaß']] = levenshtein_distance(hs1[i], hs2[k[1]])
    else:
        df.loc[df['Vers_ID'] == i, ['Ähnlichkeitsmaß']] = 'n.a.'
df.to_csv('uebersicht.csv', index=False)


#TODO: Ähnlichkeitsmaß anpassen!
#df['Vorschlag_Zuordnung_Vers_ID'],df['Vorschlag_Zuordnung_Vers'] = pd.DataFrame([[Vorschlag_Zuordnung_Vers_ID[0], Vorschlag_Zuordnung_Vers_ID[1]]], index=df.index)


not_found = sorted(set(list([i for i in range(len(hs2))])).difference(list(df['Vorschlag_Zuordnung_Vers_ID'])))
indices = df['Vorschlag_Zuordnung_Vers_ID'].tolist()

def not_found_v(not_found, indices):
    result = {}
    for i in not_found:
        if i % 2 == 0:
            if i + 1 in indices and indices[indices.index(i+1)-1] == 'n.a.':
                result[indices.index(i+1)-1] = [hs2[i], i, '* Nicht zugeordneter Vers']
                indices[indices.index(i+1)-1] = i
            elif i - 1 in indices and indices[indices.index(i-1)+1] == 'n.a.':
                result[indices.index(i-1)+1] = [hs2[i], i, '* Nicht zugeordneter Vers']
                indices[indices.index(i-1)+1] = i
        else:
            if i - 1 in indices and indices[indices.index(i-1)+1] == 'n.a.':
                result[indices.index(i-1)+1] = [hs2[i], i, '* Nicht zugeordneter Vers']
                indices[indices.index(i-1)+1] = i

            elif i + 1 in indices and indices[indices.index(i+1)-1] == 'n.a.':
                result[indices.index(i+1)-1] = [hs2[i], i, '* Nicht zugeordneter Vers']
                indices[indices.index(i+1)-1] = i

    return result

result_not_f = not_found_v(not_found, indices)

for k,v in result_not_f.items():
    if isinstance(v[-1], str):
        df.loc[df['Vers_ID'] == k, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung', 'Ähnlichkeitsmaß']] = v[0], v[1], v[-1], levenshtein_distance(hs1[k],v[0])
    else:
        df.loc[df['Vers_ID'] == k, ['Vorschlag_Zuordnung_Vers', 'Vorschlag_Zuordnung_Vers_ID', 'Anmerkung']] = v[0], v[1], 'n.a.'

df.to_csv('uebersicht.csv', index=False)



nf = sorted(set(list([i for i in range(len(hs2))])).difference(list(df['Vorschlag_Zuordnung_Vers_ID'])))
print(nf)
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

col_df = df.style.apply(color_rule, axis=1, subset=['Ähnlichkeitsmaß'])

col_df.to_excel(r'styled.xlsx')
