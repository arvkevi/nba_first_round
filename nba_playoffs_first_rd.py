import pandas as pd
import requests

from bs4 import BeautifulSoup
from collections import Counter


def series_winner(seriesdf):
    """given a DataFrame of NBA playoff series outcomes, return who the winner in five would have been as well as the winner in seven"""
    series_tracker = Counter()
    for i, game in seriesdf.iterrows():
        game_no = i+1
        series_tracker[game['game_winning_team']]+=1
        #print(game_no, game['game_winning_team'], series_tracker, max(series_tracker, key=series_tracker.get))
        if any(games_won == 3 for games_won in series_tracker.values()) and game_no <= 5:
            best_of_five_winner = max(series_tracker, key=series_tracker.get)
        elif any(games_won > 3 for games_won in series_tracker.values()) and game_no >= 4:
            best_of_seven_winner = max(series_tracker, key=series_tracker.get)
            best_of_seven_loser = min(series_tracker, key=series_tracker.get)
    return best_of_five_winner, best_of_seven_winner, best_of_seven_loser

if __name__ == '__main__':
    years = range(2003, 2019)
    df = pd.DataFrame()
    for year in years:
        url_to_scrape = 'https://www.basketball-reference.com/playoffs/NBA_{}.html'.format(year)
        r = requests.get(url_to_scrape)
        soup = BeautifulSoup(r.text)

        table = soup.find(attrs={'id': 'all_playoffs'})
        table_body = table.find('tbody')
        pseudo_headers = table.find_all(attrs={'class': 'tooltip opener'})
        sub_tables = table_body.find_all('tr', attrs={'class': 'toggleable'})

        for header, tbl in zip(pseudo_headers, sub_tables):
            if 'First Round' in header.string:
                serdf = pd.read_html(str(tbl), flavor='bs4')[0]
                serdf.columns = ['game', 'date', 'home_team', 'home_team_score', 'away_team', 'away_team_score']
                serdf['year'] = year
                # create a series id
                teams = pd.unique(serdf['home_team'])
                serdf['series_id'] = '{}_{}_{}'.format(teams[0].replace(' ', ''), teams[1].replace(' ', ''), year)
                # clean up away team name
                serdf['away_team'] = serdf['away_team'].str.replace('@ ', '')
                # assign a winning team column
                serdf['game_winner_column'] = serdf[['home_team_score', 'away_team_score']].idxmax(axis=1).str.replace(
                    '_score', '')
                serdf['game_winning_team'] = serdf.apply(lambda row: row[row['game_winner_column']], axis=1)

                # who would've won in a five game series, who did win the seven game series
                best_five, best_seven, best_seven_loser = series_winner(serdf)
                serdf['best_of_five_winner'] = best_five
                serdf['best_of_seven_winner'] = best_seven
                serdf['best_of_seven_loser'] = best_seven_loser
                df = df.append(serdf)

    df['series_too_long'] = df['best_of_seven_winner'] == df['best_of_five_winner']
    df.to_csv('nba_playoffs_first_round.csv', index=False)