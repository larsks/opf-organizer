import fnmatch
import logging
import yaml

from functools import wraps
from pathlib import Path

from opf_organizer.exc import (
    InvalidResourceType,
    NotAResource,
    OrganizerError,
    UnknownResourceType,
)

LOG = logging.getLogger()


def validate_doc(func):
    @wraps(func)
    def wrapper(self, doc, *args, **kwargs):
        if any(attr not in doc for attr in ['apiVersion', 'kind']):
            raise NotAResource()
        return func(self, doc, *args, **kwargs)

    return wrapper


class Organizer:
    skip_patterns = [
        'kustomize.config.k8s.io/*',
    ]

    def __init__(self, dest, resources):
        self.dest = Path(dest)
        self.resources = resources

        self._gen_resmap()

    def _gen_resmap(self):
        self.resmap = resmap = {}
        for resource in self.resources:
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

        target = (
            self.dest /
            resource['apiGroup'] /
            resource['name'] /
            '{}.yaml'.format(doc['metadata']['name'])
        )

        return target

    def organize(self, doc):
        target = self.target_for(doc)
        target.parent.mkdir(parents=True, exist_ok=True)
        LOG.info('writing to %s', target)
        with target.open('w') as fd:
            yaml.safe_dump(doc, fd)

    def organize_many(self, docs, filename='<none>'):
        for docnum, doc in enumerate(docs):
            try:
                self.organize(doc)
            except OrganizerError as err:
                LOG.warning('%s.%d: skipped: %s',
                            filename, docnum, err)
                continue
