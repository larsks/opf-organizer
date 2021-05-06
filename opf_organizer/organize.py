#!/usr/bin/python

import click
import json
import logging
import os
import pkg_resources
import yaml

from pathlib import Path

LOG = logging.getLogger()


@click.command(context_settings={'auto_envvar_prefix': 'OPF_ORGANIZER'})
@click.option('-r', '--resources', 'resources_file',
              type=click.File(mode='r'),
              default=pkg_resources.resource_stream(__name__, 'data/resources.json'))
@click.option('-n', '--dryrun',
              is_flag=True)
@click.option('-k', '--clean',
              count=True)
@click.option('-d', '--dest')
@click.argument('source')
def organize(resources_file, dryrun, clean, source, dest):
    if not dest:
        dest = source

    with resources_file:
        resources = json.load(resources_file)
        LOG.debug('read %d api resources from %s',
                  len(resources), resources_file.name)

    resmap = {}
    for resource in resources:
        # I don't know what these are but they throw everything off.
        if '/' in resource['name']:
            continue

        resmap['{apiGroup}/{kind}'.format(**resource)] = resource

    for dirpath, dirnames, filenames in os.walk(source):
        for filename in filenames:
            manifest = Path(dirpath) / filename

            if manifest.name == 'kustomization.yaml':
                if clean > 0:
                    LOG.info('removing %s', manifest)
                    if not dryrun:
                        manifest.unlink()
                continue

            if manifest.suffix == '.yaml':
                with manifest.open() as fd:
                    docs = yaml.safe_load_all(fd)

                    for doc in docs:
                        try:
                            apigroup, version = doc['apiVersion'].split('/')
                        except ValueError:
                            apigroup = 'core'

                        reskey = '{apigroup}/{kind}'.format(
                            apigroup=apigroup, **doc)
                        resource = resmap[reskey]

                        target = (
                            Path(dest) /
                            resource['apiGroup'] /
                            resource['name'] /
                            '{}.yaml'.format(doc['metadata']['name'])
                        )

                        LOG.info('writing %s (from %s)',
                                 target, manifest)
                        if not dryrun:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with target.open('w') as fd:
                                yaml.safe_dump(doc, fd)

                if not dryrun and clean > 1:
                    LOG.info('removing %s', manifest)
                    manifest.unlink()
