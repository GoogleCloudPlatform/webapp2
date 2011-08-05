
class BaseAction(object):
    """Base interface for custom actions."""

    #: Reference to :class:`Manager`.
    manager = None
    #: Action name.
    name = None
    #: ArgumentParser description.
    description = None
    #: ArgumentParser epilog.
    epilog = None

    def __init__(self, manager):
        raise NotImplementedError()

    def __call__(self, argv):
        raise NotImplementedError()


class Action(object):

    def __init__(self, manager):
        self.manager = manager
