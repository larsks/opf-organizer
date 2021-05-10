class OrganizerError(Exception):
    def __str__(self):
        return self.__doc__


class InvalidResourceType(OrganizerError):
    '''Invalid resource type'''


class UnknownResourceType(OrganizerError):
    '''Unknown resource type'''


class NotAResource(OrganizerError):
    '''Not a Kubernetes resources'''


class NamespacedResource(OrganizerError):
    '''Can't organize namespaced resources'''


class FileExists(OrganizerError):
    '''Destination file already exists'''
