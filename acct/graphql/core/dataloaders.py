from collections.abc import Iterable

from promise import Promise
from promise.dataloader import DataLoader as BaseLoader

from acct.graphql.core.context import AcctContext


class DataLoader[K, R](BaseLoader):
    context_key: str
    context: AcctContext

    def __new__(cls, context: AcctContext):
        key = cls.context_key
        if key is None:
            raise TypeError(f"Data loader {cls} does not define a context key")
        if not hasattr(context, "dataloaders"):
            context.dataloaders = {}
        if key not in context.dataloaders:
            context.dataloaders[key] = super().__new__(cls)
        loader = context.dataloaders[key]
        assert isinstance(loader, cls)
        return loader

    def __init__(self, context: AcctContext) -> None:
        if getattr(self, "context", None) != context:
            self.context = context
            super().__init__()

    def batch_load_fn(self, keys: Iterable[K]) -> Promise[list[R]]:
        results = self.batch_load(keys)

        if not isinstance(results, Promise):
            return Promise.resolve(results)

        def did_fulfill(results: list[R]) -> list[R]:
            return results

        def did_reject(error: Exception) -> list[R]:
            raise error

        return results.then(did_fulfill, did_reject)

    def batch_load(self, keys: Iterable[K]) -> Promise[list[R]] | list[R]:
        raise NotImplementedError()
