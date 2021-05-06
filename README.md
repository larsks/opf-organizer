# Organize manifests by api group and resource name

Clone this repository, then:

```
python -m opf_organizer organize-tree <src>
```

This will recursively walk `<src>` looking for YAML manifests. It will
re-write them to paths determined by the api group
and resource type.

By default, `opf_organizer` will not remove any files. To remove all
`kustomization.yaml` files, specify `-k`. To also remove source
manifests after writing them to a new location, specify `-kk`.

For example, the following would rewrite `cluster-scope/base` in
place, removing both `kustomization.yaml` files and original
manifests:

```
python -m opf_organizer organize-tree -kk ../apps/cluster-scope/base
```

To put reorganized files in a new directory tree, there is a `--dest`
option:

```
python -m opf_organizer organize-tree \
  --dest ../apps/cluster-scope/newbase \
  ../apps/cluster-scope/base
```

If you organize files "in place", you'll end up with a bunch of empty
directories. You can clean those up by running:

```
find ../apps/cluster-scope/base -type d -print | xargs rmdir
```

## Organizing individual files

The `organize-files` command will read individual files (or from
*stdin* if no filenames are provided), and will write content from
that input to appropriate locations. It will not remove the source
file(s).  For example:

```
curl https://raw.githubusercontent.com/operate-first/apps/master/cluster-scope/base/clusterroles/argocd-application-controller/clusterrole.yaml |
python -m opf_organizer -v organize-files -d ../apps/cluster-scope/newbase
```

## Regenerating resource cache

This package has an api resources cache in `data/resources.json`. You
can generate a new version of this file with the `resources` command:

```
python -m opf_organizer resources -o resources.json
```

You can use the updated cache with the `--resources` option to the
`organize` command:

```
python -m opf_organizer organize --resources resources.json ...
```
