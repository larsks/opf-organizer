import logging
import yaml

from pathlib import Path

LOG = logging.getLogger()


class Organizer:
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

    def target_for(self, doc):
        try:
            apigroup, version = doc['apiVersion'].split('/')
        except ValueError:
            apigroup = 'core'

        reskey = '{apigroup}/{kind}'.format(
            apigroup=apigroup, **doc)
        resource = self.resmap[reskey]

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
