class OrganizerError(Exception):
    def __str__(self):
        return self.__doc__


class InvalidResourceType(OrganizerError):
    '''Invalid resource type'''


class UnknownResourceType(OrganizerError):
    '''Unknown resource type'''


class NotAResource(OrganizerError):
    '''Not a Kubernetes resources'''
