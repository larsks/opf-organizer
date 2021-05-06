import click
import csv
import json
import kubernetes
import sys

from openshift.dynamic import DynamicClient
from tabulate import tabulate, tabulate_formats


def OutputFormatType(v):
    if v in ['table', 'json', 'csv', 'none']:
        return v

    raise ValueError(v)


def TableFormatType(v):
    if v in tabulate_formats or v == 'help':
        return v

    raise ValueError(v)


@click.command()
@click.option('-t', '--table-format',
              default='plain',
              type=TableFormatType)
@click.option('-f', '--format',
              default='json',
              type=OutputFormatType)
@click.option('-o', '--output',
              default=sys.stdout,
              type=click.File(mode='w'))
def resources(table_format, format, output):
    if table_format == 'help':
        print('\n'.join(tabulate_formats))
        return

    k8s_client = kubernetes.config.new_client_from_config()
    oc = DynamicClient(k8s_client)

    apis = oc.request('GET', '/apis')
    core_resources = oc.request('GET', '/api/v1')

    resources = []
    for resource in core_resources['resources']:
        data = {k: v for k, v in resource.items()
                if k in ['kind', 'name', 'namespaced']}
        data['apiVersion'] = 'v1'
        data['apiGroup'] = 'core'
        resources.append(data)

    for group in apis['groups']:
        name = group['name']
        for version in group['versions']:
            ver = version['version']
            apiresources = oc.request('GET', f'/apis/{name}/{ver}')
            for resource in apiresources['resources']:
                data = {k: v for k, v in resource.items()
                        if k in ['kind', 'name', 'namespaced']}
                data['apiVersion'] = ver
                data['apiGroup'] = name
                resources.append(data)

    with output:
        if format == 'json':
            output.write(json.dumps(resources, indent=2))
        elif format == 'table':
            output.write(tabulate(resources, tablefmt=table_format))
        elif format == 'csv':
            writer = csv.DictWriter(output, resources[0].keys())
            for resource in resources:
                writer.writerow(resource)
