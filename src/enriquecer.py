import json
from pathlib import Path
import pandas as pd
import config

ROOT = Path(__file__).resolve().parents[3]
PRATA = config.PRATA
# Preencha com o mapeamento completo entre os nomes de partidas.parquet -> player_valuations.parquet
DE_PARA_PARTIDAS = {
    # BRASIL (BRA)
    "America MG": "América Futebol Clube (MG)",
    "Athletico-PR": "Club Athletico Paranaense",
    "Atletico GO": "Atlético Clube Goianiense",
    "Atletico-MG": "Clube Atlético Mineiro",
    "Avai": "Avaí FC",
    "Bahia": "Esporte Clube Bahia",
    "Botafogo RJ": "Botafogo de Futebol e Regatas",
    "Bragantino": "Red Bull Bragantino",
    "CSA": "Centro Sportivo Alagoano (AL)",
    "Ceara": "Ceará Sporting Club",
    "Chapecoense-SC": "Associação Chapecoense de Futebol",
    "Corinthians": "Sport Club Corinthians Paulista",
    "Coritiba": "Coritiba Foot Ball Club",
    "Criciuma": "Criciúma Esporte Clube",
    "Cruzeiro": "Cruzeiro Esporte Clube",
    "Cuiaba": "Cuiabá Esporte Clube (MT)",
    "Figueirense": "Figueirense Futebol Clube",
    "Flamengo RJ": "CR Flamengo",
    "Fluminense": "Fluminense Football Club",
    "Fortaleza": "Fortaleza Esporte Clube",
    "Goias": "Goiás EC",
    "Gremio": "Grêmio Foot-Ball Porto Alegrense",
    "Internacional": "Sport Club Internacional",
    "Joinville": "Joinville Esporte Clube (SC)",
    "Juventude": "Esporte Clube Juventude",
    "Nautico": "Clube Náutico Capibaribe",
    "Palmeiras": "Sociedade Esportiva Palmeiras",
    "Parana": "Paraná Clube",
    "Ponte Preta": "Associação Atlética Ponte Preta",
    "Portuguesa": "Portuguesa",
    "Santa Cruz": "Santa Cruz Futebol Clube (PE)",
    "Santos": "Santos FC",
    "Sao Paulo": "São Paulo Futebol Clube",
    "Sport Recife": "Sport Club do Recife",
    "Vasco": "Clube de Regatas Vasco da Gama",
    "Vitoria": "Esporte Clube Vitória",

    # ALEMANHA (D1)
    "Augsburg": "FC Augsburg",
    "Bayern Munich": "Bayern Munich",
    "Bochum": "VfL Bochum",
    "Braunschweig": "Eintracht Braunschweig",
    "Darmstadt": "SV Darmstadt 98",
    "Dortmund": "Borussia Dortmund",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "FC Koln": "1.FC Köln",
    "Fortuna Dusseldorf": "Fortuna Düsseldorf",
    "Freiburg": "SC Freiburg",
    "Greuther Furth": "SpVgg Greuther Fürth",
    "Hamburg": "Hamburger SV",
    "Hannover": "Hannover 96",
    "Heidenheim": "1.FC Heidenheim 1846",
    "Hertha": "Hertha BSC",
    "Hoffenheim": "TSG 1899 Hoffenheim",
    "Holstein Kiel": "Holstein Kiel",
    "Ingolstadt": "FC Ingolstadt 04",
    "Kaiserslautern": "1.FC Kaiserslautern",
    "Leverkusen": "Bayer 04 Leverkusen",
    "M'gladbach": "Borussia Mönchengladbach",
    "MGladbach": "Borussia Mönchengladbach",
    "Mainz": "1.FSV Mainz 05",
    "Nurnberg": "1.FC Nuremberg",
    "Paderborn": "SC Paderborn 07",
    "RB Leipzig": "RB Leipzig",
    "Schalke 04": "FC Schalke 04",
    "St Pauli": "FC St. Pauli",
    "Stuttgart": "VfB Stuttgart",
    "Union Berlin": "1.FC Union Berlin",
    "Werder Bremen": "SV Werder Bremen",
    "Wolfsburg": "VfL Wolfsburg",

    # INGLATERRA (E0)
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa",
    "Birmingham": "Birmingham City",
    "Blackburn": "Blackburn Rovers",
    "Blackpool": "Blackpool FC",
    "Bolton": "Bolton Wanderers",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion",
    "Burnley": "Burnley FC",
    "Cardiff": "Cardiff City",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Ipswich": "Ipswich Town",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Liverpool": "Liverpool FC",
    "Luton": "Luton Town",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Middlesbrough": "Middlesbrough FC",
    "Newcastle": "Newcastle United",
    "Norwich": "Norwich City",
    "Nott'm Forest": "Nottingham Forest",
    "Nottm Forest": "Nottingham Forest",
    "QPR": "Queens Park Rangers",
    "Reading": "Reading FC",
    "Sheffield United": "Sheffield United",
    "Southampton": "Southampton FC",
    "Stoke": "Stoke City",
    "Sunderland": "Sunderland AFC",
    "Swansea": "Swansea City",
    "Tottenham": "Tottenham Hotspur",
    "Watford": "Watford FC",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wigan": "Wigan Athletic",
    "Wolves": "Wolverhampton Wanderers",

    # FRANÇA (F1)
    "Ajaccio": "AC Ajaccio",
    "Ajaccio GFCO": "GFC Ajaccio",
    "Amiens": "Amiens SC",
    "Angers": "Angers SCO",
    "Arles": "AC Arles-Avignon",
    "Auxerre": "AJ Auxerre",
    "Bastia": "SC Bastia",
    "Bordeaux": "FC Girondins Bordeaux",
    "Brest": "Stade Brestois 29",
    "Caen": "SM Caen",
    "Clermont": "Clermont Foot 63",
    "Dijon": "Dijon FCO",
    "Evian Thonon Gaillard": "FC Évian Thonon Gaillard",
    "Guingamp": "EA Guingamp",
    "Le Havre": "Le Havre AC",
    "Lens": "RC Lens",
    "Lille": "LOSC Lille",
    "Lorient": "FC Lorient",
    "Lyon": "Olympique Lyon",
    "Marseille": "Olympique Marseille",
    "Metz": "FC Metz",
    "Monaco": "AS Monaco",
    "Montpellier": "Montpellier HSC",
    "Nancy": "AS Nancy-Lorraine",
    "Nantes": "FC Nantes",
    "Nice": "OGC Nice",
    "Nimes": "Nîmes Olympique",
    "Paris FC": "Paris FC",
    "Paris SG": "Paris Saint-Germain",
    "Reims": "Stade Reims",
    "Rennes": "Stade Rennais FC",
    "Sochaux": "FC Sochaux-Montbéliard",
    "St Etienne": "AS Saint-Étienne",
    "Strasbourg": "RC Strasbourg Alsace",
    "Toulouse": "FC Toulouse",
    "Troyes": "ESTAC Troyes",
    "Valenciennes": "Valenciennes FC",

    # ITÁLIA (I1)
    "Atalanta": "Atalanta BC",
    "Bari": "AS Bari",
    "Benevento": "Benevento Calcio",
    "Bologna": "Bologna FC 1909",
    "Brescia": "Brescia Calcio",
    "Cagliari": "Cagliari Calcio",
    "Carpi": "AC Carpi",
    "Catania": "Catania FC",
    "Cesena": "AC Cesena",
    "Chievo": "Chievo Verona",
    "Como": "Como 1907",
    "Cremonese": "US Cremonese",
    "Crotone": "FC Crotone",
    "Empoli": "FC Empoli",
    "Fiorentina": "ACF Fiorentina",
    "Frosinone": "Frosinone Calcio",
    "Genoa": "Genoa CFC",
    "Inter": "Inter Milan",
    "Juventus": "Juventus FC",
    "Lazio": "SS Lazio",
    "Lecce": "US Lecce",
    "Livorno": "AS Livorno",
    "Milan": "AC Milan",
    "Monza": "AC Monza",
    "Napoli": "SSC Napoli",
    "Novara": "Novara FC",
    "Palermo": "US Palermo",
    "Parma": "Parma Calcio 1913",
    "Pescara": "Delfino Pescara 1936",
    "Pisa": "Pisa Sporting Club",
    "Roma": "AS Roma",
    "Salernitana": "US Salernitana 1919",
    "Sampdoria": "UC Sampdoria",
    "Sassuolo": "US Sassuolo",
    "Siena": "AC Siena",
    "Spal": "SPAL",
    "Spezia": "Spezia Calcio",
    "Torino": "Torino FC",
    "Udinese": "Udinese Calcio",
    "Venezia": "Venezia FC",
    "Verona": "Hellas Verona",

    # ESPANHA (SP1)
    "Alaves": "Deportivo Alavés",
    "Almeria": "UD Almería",
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atlético de Madrid",
    "Barcelona": "FC Barcelona",
    "Betis": "Real Betis Balompié",
    "Cadiz": "Cádiz CF",
    "Celta": "Celta de Vigo",
    "Cordoba": "Córdoba CF",
    "Eibar": "SD Eibar",
    "Elche": "Elche CF",
    "Espanol": "RCD Espanyol Barcelona",
    "Getafe": "Getafe CF",
    "Girona": "Girona FC",
    "Granada": "Granada CF",
    "Hercules": "Hércules CF",
    "Huesca": "SD Huesca",
    "La Coruna": "Deportivo de La Coruña",
    "Las Palmas": "UD Las Palmas",
    "Leganes": "CD Leganés",
    "Levante": "Levante UD",
    "Malaga": "Málaga CF",
    "Mallorca": "RCD Mallorca",
    "Osasuna": "CA Osasuna",
    "Oviedo": "Real Oviedo",
    "Real Madrid": "Real Madrid",
    "Santander": "Racing Santander",
    "Sevilla": "Sevilla FC",
    "Sociedad": "Real Sociedad",
    "Sp Gijon": "Sporting Gijón",
    "Valencia": "Valencia CF",
    "Valladolid": "Real Valladolid CF",
    "Vallecano": "Rayo Vallecano",
    "Villarreal": "Villarreal CF",
    "Zaragoza": "Real Zaragoza",
}

# Unifica nomes históricos/alternativos que o Transfermarkt usa para o mesmo clube
DE_PARA_TRANSFERMARKT = {
    "Atlético Paranaense": "Club Athletico Paranaense",
    "Clube Atlético Bragantino (SP)": "Red Bull Bragantino",
    "Santa Cruz FC (PE)": "Santa Cruz Futebol Clube (PE)",
    "SSC Bari": "AS Bari",
    "Cesena FC": "AC Cesena",
    "Calcio Como": "Como 1907",
    "Empoli FC": "FC Empoli",
    "FC Internazionale": "Inter Milan",
    "US Livorno 1915": "AS Livorno",
    "Palermo FC": "US Palermo",
    "Parma FC": "Parma Calcio 1913",
    "AC Pisa 1909": "Pisa Sporting Club",
    "ACN Siena": "AC Siena",
    "SPAL 2013": "SPAL",
}

# Lista completa para filtrar player_valuations_20260924.csv na Prata
TODOS_CLUBES_TRANSFERMARKT = set(DE_PARA_PARTIDAS.values()) | set(DE_PARA_TRANSFERMARKT.keys())

def adicionar_temporada_partidas(df):
    df = df.copy()
    df["MatchDate"] = pd.to_datetime(df["MatchDate"])
    ano = df["MatchDate"].dt.year
    mes = df["MatchDate"].dt.month
    dia = df["MatchDate"].dt.day

    inicio_temporada_europeia = (
        (mes > 7) | ((mes == 7) & (dia >= 25))
        )

    temp_europa = ano.where(inicio_temporada_europeia, ano - 1)
    df["temporada"] = temp_europa.where(df["Division"] != "BRA", ano).astype(str)
    df["temporada"] = temp_europa.where(df["Division"] != "BRA", ano).astype(str)
    df["home_padrao"] = df["HomeTeam"].replace(DE_PARA_PARTIDAS)
    df["away_padrao"] = df["AwayTeam"].replace(DE_PARA_PARTIDAS)
    return df

def agregar_elencos(df_val):
    df_val = df_val.copy()
    df_val["temporada"] = df_val["temporada"].astype(str)
    df_val["clube_padrao"] = df_val["current_club_name"].replace(DE_PARA_TRANSFERMARKT)
    return (
        df_val.groupby(["clube_padrao", "temporada"], as_index=False)
        .agg(valor_total_elenco=("market_value_in_eur", "sum"))
    )


def main():
    partidas = pd.read_parquet(PRATA / "partidas.parquet")
    valuations = pd.read_parquet(PRATA / "player_valuations.parquet")

    partidas = adicionar_temporada_partidas(partidas)
    elencos = agregar_elencos(valuations)

    # Passo 1: Conferência de chaves antes da junção
    chaves_part = set(zip(partidas["home_padrao"], partidas["temporada"])) | set(
        zip(partidas["away_padrao"], partidas["temporada"])
    )
    chaves_val = set(zip(elencos["clube_padrao"], elencos["temporada"]))
    print("Só em partidas:", len(chaves_part - chaves_val))
    print("Só em valuations:", len(chaves_val - chaves_part))
    print("Nos dois:", len(chaves_part & chaves_val))

    # Passo 2: Junção left trazendo apenas a soma do elenco mandante e visitante
    enriquecido = (
        partidas.merge(
            elencos.rename(columns={"valor_total_elenco": "valor_total_elenco_home"}),
            left_on=["home_padrao", "temporada"],
            right_on=["clube_padrao", "temporada"],
            how="left",
            validate="many_to_one",
        )
        .drop(columns=["clube_padrao"])
        .merge(
            elencos.rename(columns={"valor_total_elenco": "valor_total_elenco_away"}),
            left_on=["away_padrao", "temporada"],
            right_on=["clube_padrao", "temporada"],
            how="left",
            validate="many_to_one",
        )
        .drop(columns=["clube_padrao"])
    )

    # Passo 3: Validação de contagem e sem par
    assert len(enriquecido) == len(partidas), "O grão da tabela mudou!"
    sem_par_home = int(enriquecido["valor_total_elenco_home"].isna().sum())
    sem_par_away = int(enriquecido["valor_total_elenco_away"].isna().sum())
    print(f"Partidas: {len(partidas)} | Sem par Home: {sem_par_home} | Sem par Away: {sem_par_away}")

    # Passo 5: Atributos derivados pós-junção
    enriquecido["diferenca_valor_elenco"] = (
        enriquecido["valor_total_elenco_home"] - enriquecido["valor_total_elenco_away"]
    )
    enriquecido["razao_valor_elenco"] = (
        enriquecido["valor_total_elenco_home"] / enriquecido["valor_total_elenco_away"]
    )
    
    destino_parquet = PRATA / "partidas_enriquecidas.parquet"
    destino_csv = PRATA / "partidas_enriquecidas.csv"
    enriquecido.to_parquet(destino_parquet, index=False)
    enriquecido.to_csv(destino_csv, index=False)
    print("Salvo em:", destino_parquet, enriquecido.shape)

if __name__ == "__main__":
    main()