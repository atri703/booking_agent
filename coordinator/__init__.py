"""Optional A2A coordinator."""


def __getattr__(name):
    if name == "agent":
        import importlib

        return importlib.import_module(__name__ + ".agent")
    raise AttributeError(name)
