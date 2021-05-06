import click
import json
import logging
import pkg_resources

from opf_organizer.cmd.organize import organize_tree, organize_files
from opf_organizer.cmd.resources import resources

LOG = logging.getLogger(__name__)


@click.group(context_settings={'auto_envvar_prefix': 'OPF_ORGANIZER'})
@click.option('-v', '--verbose',
              count=True,
              type=click.IntRange(0, 2))
@click.option('-r', '--resources', 'resources_file',
              type=click.File(mode='r'),
              default=pkg_resources.resource_stream(
                  __name__, 'data/resources.json'))
@click.pass_context
def main(ctx, verbose, resources_file):
    loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    logging.basicConfig(level=loglevel)

    with resources_file:
        ctx.obj = json.load(resources_file)
        LOG.debug('read %d api resources from %s',
                  len(ctx.obj), resources_file.name)


main.add_command(organize_tree)
main.add_command(organize_files)
main.add_command(resources)
