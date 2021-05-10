import contextlib
import fnmatch
import json
import logging
import pkg_resources
import os
import yaml

from functools import wraps
from pathlib import Path

from opf_organizer.exc import (
    FileExists,
    InvalidResourceType,
    NotAResource,
    OrganizerError,
    UnknownResourceType,
)

KUSTOMIZE_KIND = 'Kustomization'
KUSTOMIZE_API_VERSION = 'kustomize.config.k8s.io/v1beta1'
LOG = logging.getLogger()


yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str


def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
    return dumper.org_represent_str(data)


yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)


def validate_doc(func):
    @wraps(func)
    def wrapper(self, doc, *args, **kwargs):
        if any(attr not in doc for attr in ['apiVersion', 'kind']):
            raise NotAResource()
        return func(self, doc, *args, **kwargs)

    return wrapper


def get_api_resources(path=None):
    if not path:
        path = os.environ.get('OPF_API_RESOURCES')

    if path:
        fd = open(path, 'r')
    else:
        fd = pkg_resources.resource_stream(
            'opf_organizer', 'data/resources.json')

    with fd:
        resources = json.load(fd)

    return resources


class Organizer:
    skip_patterns = [
        'kustomize.config.k8s.io/*',
    ]

    def __init__(self, dest,
                 config=None,
                 api_resources=None,
                 kustomize=True):
        self.dest = Path(dest)
        self.kustomize = kustomize
        self.config = config

        if api_resources:
            self.api_resources = api_resources
        else:
            self.api_resources = get_api_resources(config.api_resources_path)

        self._gen_resmap()

    def _gen_resmap(self):
        self.resmap = resmap = {}
        for resource in self.api_resources:
            # I don't know what these are but they throw everything off.
            if '/' in resource['name']:
                continue

            resmap['{apiGroup}/{kind}'.format(**resource)] = resource

    @validate_doc
    def group_for(self, doc):
        try:
            apigroup, version = doc['apiVersion'].split('/')
        except ValueError:
            apigroup = 'core'

        return apigroup

    @validate_doc
    def target_for(self, doc):
        apigroup = self.group_for(doc)

        reskey = '{apigroup}/{kind}'.format(
            apigroup=apigroup, **doc)

        if any(fnmatch.fnmatch(reskey, pattern) for pattern in self.skip_patterns):
            raise InvalidResourceType()

        try:
            resource = self.resmap[reskey]
        except KeyError:
            raise UnknownResourceType()

        if 'namespaced' in self.config.warnings and resource['namespaced']:
            LOG.warning('%s: organizing namespaced resource',
                        reskey)

        target = (
            self.dest /
            resource['apiGroup'] /
            resource['name'] /
            doc['metadata']['name'] /
            '{}.yaml'.format(doc['kind'].lower())
        )

        return target

    def _write_kustomization(self, target, kustomization):
        kustom = target.parent / 'kustomization.yaml'
        LOG.info('writing kustomization to %s', kustom)
        with kustom.open('w') as fd:
            if kustomization:
                data = kustomization
            else:
                data = {}

            data.update({
                'apiVersion': KUSTOMIZE_API_VERSION,
                'kind': KUSTOMIZE_KIND,
                'resources': [target.name],
            })

            yaml.safe_dump(data, fd)

    def organize_path(self, path, doc, kustomization=None):
        target = self.target_for(doc)

        if target.exists() and not self.config.force:
            raise FileExists()

        target.parent.mkdir(parents=True, exist_ok=True)
        LOG.info('writing %s to %s', path, target)
        with path.open('r') as srcfd, target.open('w') as dstfd:
            while True:
                data = srcfd.read(8192)
                if not data:
                    break
                dstfd.write(data)

        if self.kustomize:
            self._write_kustomization(target, kustomization)

    def organize_doc(self, doc, kustomization=None, path=None):
        target = self.target_for(doc)

        if target.exists() and not self.config.force:
            raise FileExists()

        target.parent.mkdir(parents=True, exist_ok=True)
        LOG.info('writing resource to %s', target)
        with target.open('w') as fd:
            yaml.safe_dump(doc, fd)

        if self.kustomize:
            self._write_kustomization(target, kustomization)

    def organize_many(self, docs, path=None, kustomization=None):
        for docnum, doc in enumerate(docs):
            try:
                self.organize_doc(doc, path=path, kustomization=kustomization)
            except OrganizerError as err:
                LOG.warning('%s.%d: skipped: %s',
                            path if path else '<none>', docnum, err)
                continue
