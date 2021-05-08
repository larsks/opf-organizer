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
@click.option('--kustomize/--no-kustomize', default=True)
@click.argument('source')
@click.pass_obj
def organize_tree(config, clean, dest, kustomize, source):
    if not dest:
        dest = source

    organizer = Organizer(dest,
                          kustomize=kustomize,
                          api_resources_path=config.api_resources_path)

    for dirpath, dirnames, filenames in os.walk(source):
        if 'kustomization.yaml' in filenames:
            path = Path(dirpath) / 'kustomization.yaml'
            with path.open() as fd:
                kustomization = yaml.safe_load(fd)
            if clean > 0:
                LOG.info('removing %s', path)
                path.unlink()

        for filename in filenames:
            manifest = Path(dirpath) / filename

            if manifest.name == 'kustomization.yaml':
                continue

            if manifest.suffix == '.yaml':
                with manifest.open() as fd:
                    try:
                        docs = yaml.safe_load_all(fd)
                        organizer.organize_many(docs,
                                                filename=manifest,
                                                kustomization=kustomization)
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
def organize_files(config, dryrun, dest, sources):
    organizer = Organizer(dest,
                          api_resources_path=config.api_resources_path)

    if not sources:
        try:
            organizer.organize_many(yaml.safe_load_all(sys.stdin), '<stdin>')
        except yaml.YAMLError as err:
            LOG.error('<stdin>: skipping: Not a valid YAML document: %s',
                      err)
    else:
        for source in sources:
            path = Path(source)
            with path.open() as fd:
                docs = yaml.safe_load_all(fd)
                try:
                    organizer.organize_many(docs, filename=path)
                except yaml.YAMLError as err:
                    LOG.error('%s: skipping: Not a valid YAML document: %s',
                              path, err)
