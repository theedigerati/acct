import datetime
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

if TYPE_CHECKING:
    from acct.graphql.core.dataloaders import DataLoader
    from acct.people.models import User


class AcctContext(HttpRequest):
    _cached_user: "User | None"
    decoded_auth_token: dict[str, Any] | None
    allow_replica: bool = True
    dataloaders: dict[str, "DataLoader"]
    user: "User | None"
    requestor: "User | None"
    request_time: datetime.datetime

    def __init__(self, *args, **kwargs):
        if "dataloaders" in kwargs:
            self.dataloaders = kwargs.pop("dataloaders")
        super().__init__(*args, **kwargs)
