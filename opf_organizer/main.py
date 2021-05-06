import click
import logging

from opf_organizer.organize import organize
from opf_organizer.resources import resources

LOG = logging.getLogger(__name__)


@click.group(context_settings={'auto_envvar_prefix': 'OPF_ORGANIZER'})
@click.option('-v', '--verbose',
              count=True,
              type=click.IntRange(0, 2))
def main(verbose):
    loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    logging.basicConfig(level=loglevel)


main.add_command(organize)
main.add_command(resources)
