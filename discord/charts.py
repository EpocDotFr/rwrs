from models import RwrAccountStat
from io import BytesIO
import matplotlib
import helpers

matplotlib.use('Agg')

from matplotlib.dates import date2num
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def create_evolution_chart(rwr_account, column, title):
    """Create an image containing a chart representing the evolution of a given player stat."""
    evolution_chart = BytesIO()

    player_evolution_data = RwrAccountStat.get_stats_for_column(rwr_account, column)

    fig, ax = plt.subplots()

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))

    if column == 'score':
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: helpers.simplified_integer(x)))

    ax.set_title(title)

    ax.plot_date(
        [date2num(data['t'].datetime) for data in player_evolution_data],
        [data['v'] for data in player_evolution_data],
        'g-'
    )

    for data in player_evolution_data:
        if not data['ptr']:
            continue

        date = date2num(data['t'].datetime)

        ax.axvline(date, color='b', linestyle=':')
        ax.text(date, data['v'], data['ptr'], rotation=90, bbox={'color': 'white'})

    ax.autoscale_view()

    ax.grid(True, which='both')

    fig.tight_layout()

    fig.savefig(evolution_chart, format='png')

    evolution_chart.seek(0)

    return evolution_chart
