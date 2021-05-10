import click
import logging
import os
import sys
import yaml

from pathlib import Path

from opf_organizer.organizer import Organizer

LOG = logging.getLogger()


def truncate_path(path, name):
    while path.name != name:
        if path == path.parent:
            break
        path = path.parent
    else:
        return path

    return None


def adjust_components(kustomization, components):
    adjusted = []
    components = Path(components)
    if 'components' in kustomization:
        for component in kustomization['components']:
            component = Path(component)
            old_comp = truncate_path(component, 'components')
            rel_path = component.relative_to(old_comp)
            newpath = components / rel_path
            adjusted.append(str(newpath))

            kustomization['components'] = adjusted


@click.command()
@click.option('-k', '--clean',
              count=True)
@click.option('-d', '--dest')
@click.option('-c', '--components-path')
@click.option('--kustomize/--no-kustomize', default=True)
@click.argument('source')
@click.pass_obj
def organize_tree(config, clean, components_path, dest, kustomize, source):
    if not dest:
        dest = source

    organizer = Organizer(dest,
                          config=config,
                          kustomize=kustomize)

    for dirpath, dirnames, filenames in os.walk(source):
        if 'kustomization.yaml' in filenames:
            path = Path(dirpath) / 'kustomization.yaml'
            with path.open() as fd:
                kustomization = yaml.safe_load(fd)
            if components_path:
                adjust_components(kustomization, components_path)
            if clean > 0:
                LOG.info('removing %s', path)
                path.unlink()
        else:
            kustomization = None

        for filename in filenames:
            manifest = Path(dirpath) / filename

            if manifest.name == 'kustomization.yaml':
                continue

            if manifest.suffix == '.yaml':
                with manifest.open() as fd:
                    try:
                        docs = yaml.safe_load_all(fd)
                        organizer.organize_many(docs,
                                                path=manifest,
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
                          config=config)

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
                    organizer.organize_many(docs, path=path)
                except yaml.YAMLError as err:
                    LOG.error('%s: skipping: Not a valid YAML document: %s',
                              path, err)
