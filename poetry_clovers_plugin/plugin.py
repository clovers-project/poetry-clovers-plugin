from poetry.plugins.application_plugin import ApplicationPlugin
from .command import CloversMainCommand, CloversPluginCommand, CloversNewCommand


class CloversApplicationPlugin(ApplicationPlugin):
    def activate(self, application):
        application.command_loader.register_factory("clovers", lambda: CloversMainCommand())
        application.command_loader.register_factory("clovers plugin", lambda: CloversPluginCommand())
        application.command_loader.register_factory("clovers new", lambda: CloversNewCommand())
