from acct.graphql.core.dataloaders import DataLoader
from acct.people.models import User


class UserByEmailLoader(DataLoader):
    context_key = "user_by_email"

    def batch_load(self, keys):
        user_map = User.objects.filter(is_active=True).in_bulk(keys, field_name="email")
        return [user_map.get(email) for email in keys]
