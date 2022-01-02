from models import RwrAccountStat
from . import constants
from io import BytesIO
from PIL import Image
import matplotlib
import helpers

matplotlib.use('Agg')

matplotlib.rcParams.update({
    'text.color': constants.TEXT_COLOR,
    'xtick.labelcolor': constants.TEXT_COLOR,
    'ytick.labelcolor': constants.TEXT_COLOR,
    'axes.labelcolor': constants.TEXT_COLOR,

    'figure.facecolor': constants.BG_COLOR_PRIMARY,

    'axes.facecolor': constants.BG_COLOR_SECONDARY,

    'axes.edgecolor': constants.BORDER_COLOR,
    'grid.color': constants.BORDER_COLOR,
})

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
        color=constants.PRIMARY_COLOR,
        linestyle='-',
        marker=''
    )

    for data in player_evolution_data:
        if not data['ptr']:
            continue

        date = date2num(data['t'].datetime)

        ax.axvline(date, color=constants.SECONDARY_COLOR, linestyle=':')
        ax.text(date, data['v'], data['ptr'], rotation=90, color=constants.TEXT_COLOR)

    ax.autoscale_view()

    ax.grid(True, which='both')

    fig.tight_layout()

    fig_midwidth = int((fig.get_figwidth() * fig.dpi) / 2)
    fig_midheight = int((fig.get_figheight() * fig.dpi) / 2)

    logo = Image.open('static/images/logo_light.png')

    logo_midwidth = int(logo.width / 2)
    logo_midheight = int(logo.height / 2)

    fig.figimage(
        logo,
        xo=fig_midwidth - logo_midwidth,
        yo=fig_midheight - logo_midheight,
        alpha=0.1
    )

    fig.savefig(evolution_chart, format='png')

    evolution_chart.seek(0)

    return evolution_chart
