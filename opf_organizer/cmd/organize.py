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
                    try:
                        docs = yaml.safe_load_all(fd)
                        organizer.organize_many(docs, filename=manifest)
                    except yaml.YAMLError as err:
                        LOG.error('%s: skipping: Not a valid YAML document: %s',
                                  manifest, err)

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
        try:
            # We transform the generator returned by safe_load_all
            # into a list so that we trigger YAML processing here
            # (where we can catch YAMLError exceptions) rather than
            # later on in the code.
            docs = list(yaml.safe_load_all(sys.stdin))
        except yaml.YAMLError as err:
            LOG.error('stdin: skipping: Not a valid YAML document: %s', err)
            raise click.Abort()
    else:
        docs = []
        for source in sources:
            path = Path(source)
            with path.open() as fd:
                try:
                    doc = yaml.safe_load_all(fd)
                    docs.extend(doc)
                except yaml.YAMLError as err:
                    LOG.error('%s: skipping: Not a valid YAML document: %s',
                              source, err)
                    continue

    organizer.organize_many(docs)
