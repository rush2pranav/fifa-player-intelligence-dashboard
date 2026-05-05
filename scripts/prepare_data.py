"""
EA FC 25 Data Preparation Script
==================================
First we will clean then combine and enrich the male + female player datasets for our Power BI project.
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


def load_and_clean(filename, gender):
    """Load the CSV and clean it"""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path, encoding='latin-1')
    
    # dropping the unnamed index colunmns
    df = df.drop(columns=[c for c in df.columns if 'Unnamed' in c], errors='ignore')
    
    # adding the gender column
    df['Gender'] = gender
    
    print(f"  {filename}: {len(df)} players loaded")
    return df


def enrich_data(df):
    """Adding the calculated columns for Power BI analysis"""
    
    # position grouping
    position_groups = {
        'GK': 'Goalkeeper',
        'CB': 'Defender', 'LB': 'Defender', 'RB': 'Defender', 'LWB': 'Defender', 'RWB': 'Defender',
        'CDM': 'Midfielder', 'CM': 'Midfielder', 'CAM': 'Midfielder', 'LM': 'Midfielder', 'RM': 'Midfielder',
        'LW': 'Forward', 'RW': 'Forward', 'CF': 'Forward', 'ST': 'Forward',
    }
    df['Position Group'] = df['Position'].map(position_groups).fillna('Other')
    
    # overall rating tier
    df['Rating Tier'] = pd.cut(
        pd.to_numeric(df['OVR'], errors='coerce'),
        bins=[0, 64, 69, 74, 79, 84, 89, 99],
        labels=['Bronze (<65)', 'Silver (65-69)', 'Low Gold (70-74)', 
                'Gold (75-79)', 'Elite (80-84)', 'World Class (85-89)', 'Icon (90+)']
    )
    
    # tier group
    df['Age Group'] = pd.cut(
        pd.to_numeric(df['Age'], errors='coerce'),
        bins=[0, 21, 25, 29, 33, 50],
        labels=['Wonderkid (≤21)', 'Rising Star (22-25)', 'Prime (26-29)', 
                'Veteran (30-33)', 'Twilight (34+)']
    )
    
    # physical metrics
    # parses the height attribute
    df['Height_cm'] = df['Height'].astype(str).str.extract(r'(\d+)').astype(float)
    
    # parses the weight attribute
    df['Weight_kg'] = df['Weight'].astype(str).str.extract(r'(\d+)').astype(float)
    
    # BMI
    df['BMI'] = (df['Weight_kg'] / ((df['Height_cm'] / 100) ** 2)).round(1)
    
    # composite scores
    # attacking scores
    for col in ['Finishing', 'Shot Power', 'Long Shots', 'Positioning', 'Volleys']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Attacking Score'] = df[['Finishing', 'Shot Power', 'Long Shots', 'Positioning', 'Volleys']].mean(axis=1).round(1)
    
    # defending scores
    for col in ['Interceptions', 'Def Awareness', 'Standing Tackle', 'Sliding Tackle', 'Heading Accuracy']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Defending Score'] = df[['Interceptions', 'Def Awareness', 'Standing Tackle', 'Sliding Tackle', 'Heading Accuracy']].mean(axis=1).round(1)
    
    # playmaking scores
    for col in ['Vision', 'Short Passing', 'Long Passing', 'Crossing', 'Curve']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Playmaking Score'] = df[['Vision', 'Short Passing', 'Long Passing', 'Crossing', 'Curve']].mean(axis=1).round(1)
    
    # physical scores
    for col in ['Acceleration', 'Sprint Speed', 'Stamina', 'Strength', 'Jumping']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Physical Score'] = df[['Acceleration', 'Sprint Speed', 'Stamina', 'Strength', 'Jumping']].mean(axis=1).round(1)
    
    # technical scores
    for col in ['Dribbling', 'Ball Control', 'Agility', 'Balance', 'Reactions']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Technical Score'] = df[['Dribbling', 'Ball Control', 'Agility', 'Balance', 'Reactions']].mean(axis=1).round(1)
    
    # versatility scores
    df['Num Alt Positions'] = df['Alternative positions'].fillna('').apply(
        lambda x: len([p for p in str(x).split(',') if p.strip()]) if pd.notna(x) and str(x).strip() else 0
    )
    
    # player archtypes
    def classify_archetype(row):
        ovr = pd.to_numeric(row.get('OVR', 0), errors='coerce') or 0
        pac = pd.to_numeric(row.get('PAC', 0), errors='coerce') or 0
        sho = pd.to_numeric(row.get('SHO', 0), errors='coerce') or 0
        pas = pd.to_numeric(row.get('PAS', 0), errors='coerce') or 0
        dri = pd.to_numeric(row.get('DRI', 0), errors='coerce') or 0
        defe = pd.to_numeric(row.get('DEF', 0), errors='coerce') or 0
        phy = pd.to_numeric(row.get('PHY', 0), errors='coerce') or 0
        
        if row.get('Position') == 'GK':
            return 'Goalkeeper'
        
        max_stat = max(pac, sho, pas, dri, defe, phy)
        if max_stat == pac:
            return 'Speedster'
        elif max_stat == sho:
            return 'Goal Scorer'
        elif max_stat == pas:
            return 'Playmaker'
        elif max_stat == dri:
            return 'Dribbler'
        elif max_stat == defe:
            return 'Destroyer'
        elif max_stat == phy:
            return 'Powerhouse'
        return 'Balanced'
    
    df['Player Archetype'] = df.apply(classify_archetype, axis=1)
    
    # league tier
    top5_leagues = ['Premier League', 'La Liga EA SPORTS', 'Serie A TIM', 
                    'Bundesliga', 'Ligue 1 McDonald\'s', 'Premier League', 'LaLiga', 'Serie A', 'Bundesliga', 'Ligue 1']
    df['Is Top 5 League'] = df['League'].isin(top5_leagues)
    
    # ensuring numeric columns
    for col in ['OVR', 'PAC', 'SHO', 'PAS', 'DRI', 'DEF', 'PHY', 'Weak foot', 'Skill moves', 'Age']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # dropping the url columns which are not required
    df = df.drop(columns=['url'], errors='ignore')
    
    return df


def main():
    print("=" * 60)
    print("EA FC 25 DATA PREPARATION FOR POWER BI")
    print("=" * 60)
    
    # loading the datasets
    print("\n--- Loading datasets ---")
    dfs = []
    
    if os.path.exists(os.path.join(DATA_DIR, 'male_players.csv')):
        dfs.append(load_and_clean('male_players.csv', 'Male'))
    if os.path.exists(os.path.join(DATA_DIR, 'female_players.csv')):
        dfs.append(load_and_clean('female_players.csv', 'Female'))
    if os.path.exists(os.path.join(DATA_DIR, 'all_players.csv')):
        if not dfs:
            dfs.append(load_and_clean('all_players.csv', 'All'))
    
    df = pd.concat(dfs, ignore_index=True)
    
    # removing the exact duplicates
    df = df.drop_duplicates(subset=['Name', 'Team', 'Position', 'OVR'], keep='first')
    
    print(f"\n  Combined: {len(df)} unique players")
    
    # enriching the data
    print("\n--- Enriching data ---")
    df = enrich_data(df)
    
    # save
    output = os.path.join(DATA_DIR, 'fc25_powerbi_ready.csv')
    df.to_csv(output, index=False)
    
    print(f"\n=== OUTPUT ===")
    print(f"Saved: {output}")
    print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    print(f"\n=== Quick Stats ===")
    print(f"Total Players: {len(df):,}")
    print(f"Male: {len(df[df['Gender']=='Male']):,}")
    print(f"Female: {len(df[df['Gender']=='Female']):,}")
    print(f"Leagues: {df['League'].nunique()}")
    print(f"Nations: {df['Nation'].nunique()}")
    print(f"Teams: {df['Team'].nunique()}")
    
    print(f"\nPosition Groups:")
    print(df['Position Group'].value_counts())
    
    print(f"\nRating Tiers:")
    print(df['Rating Tier'].value_counts().sort_index())
    
    print(f"\nAge Groups:")
    print(df['Age Group'].value_counts().sort_index())
    
    print(f"\nPlayer Archetypes:")
    print(df['Player Archetype'].value_counts())
    
    print(f"\nTop 10 Leagues by Player Count:")
    print(df['League'].value_counts().head(10))


if __name__ == '__main__':
    main()