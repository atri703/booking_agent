"""Appointment agent. Importing this package does not start servers or call models."""


def __getattr__(name):
    if name == "agent":
        import importlib

        return importlib.import_module(__name__ + ".agent")
    raise AttributeError(name)
