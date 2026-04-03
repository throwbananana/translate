from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


def load_gui_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "book_translator_gui.pyw"
    loader = SourceFileLoader("book_translator_gui_test_module", str(module_path))
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyWidget:
    def __init__(self):
        self.deleted = []
        self.inserted = []
        self.config_calls = []

    def delete(self, *args):
        self.deleted.append(args)

    def insert(self, *args):
        self.inserted.append(args)

    def config(self, **kwargs):
        self.config_calls.append(kwargs)

    def see(self, *args):
        return None


class DummyRoot:
    def __init__(self):
        self.after_calls = []

    def update(self):
        return None

    def after(self, delay, callback, *args):
        self.after_calls.append((delay, callback, args))
        return callback(*args)


class DummyTree:
    def __init__(self):
        self.deleted = []
        self.insert_calls = []

    def get_children(self):
        return ["old_item"]

    def delete(self, item):
        self.deleted.append(item)

    def insert(self, parent, index, iid=None, values=(), open=False):
        self.insert_calls.append(
            {
                "parent": parent,
                "index": index,
                "iid": iid,
                "values": values,
                "open": open,
            }
        )
        return iid or f"item_{len(self.insert_calls)}"
