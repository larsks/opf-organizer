import click
import json
import logging
import pkg_resources

from dataclasses import dataclass

from opf_organizer.cmd.organize import organize_tree, organize_files
from opf_organizer.cmd.resources import resources

LOG = logging.getLogger(__name__)


@dataclass
class Config:
    api_resources_path: str


@click.group(context_settings={'auto_envvar_prefix': 'OPF_ORGANIZER'})
@click.option('-v', '--verbose',
              count=True,
              type=click.IntRange(0, 2))
@click.option('-r', '--resources', 'resources_file')
@click.pass_context
def main(ctx, verbose, resources_file):
    loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    logging.basicConfig(level=loglevel)

    config = Config(
        api_resources_path=resources_file
    )

    ctx.obj = config


main.add_command(organize_tree)
main.add_command(organize_files)
main.add_command(resources)
