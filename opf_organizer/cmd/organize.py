import click
import logging
import os
import sys
import yaml

from pathlib import Path

from opf_organizer.organizer import Organizer

LOG = logging.getLogger()


@click.command()
@click.option('-k', '--clean',
              count=True)
@click.option('-d', '--dest')
@click.argument('source')
@click.pass_obj
def organize_tree(resources, clean, source, dest):
    if not dest:
        dest = source

    organizer = Organizer(dest, resources)

    for dirpath, dirnames, filenames in os.walk(source):
        for filename in filenames:
            manifest = Path(dirpath) / filename

            if manifest.name == 'kustomization.yaml':
                if clean > 0:
                    LOG.info('removing %s', manifest)
                    manifest.unlink()
                continue

            if manifest.suffix == '.yaml':
                with manifest.open() as fd:
                    docs = yaml.safe_load_all(fd)

                    for doc in docs:
                        organizer.organize(doc)

                if clean > 1:
                    LOG.info('removing %s', manifest)
                    manifest.unlink()


@click.command()
@click.option('-n', '--dryrun',
              is_flag=True)
@click.option('-d', '--dest', default='.')
@click.argument('sources', nargs=-1)
@click.pass_obj
def organize_files(resources, dryrun, dest, sources):
    organizer = Organizer(dest, resources)

    if not sources:
        docs = yaml.safe_load_all(sys.stdin)
    else:
        docs = []
        for source in sources:
            path = Path(source)
            with path.open() as fd:
                doc = yaml.safe_load_all(fd)
                docs.extend(doc)

    for doc in docs:
        organizer.organize(doc)
