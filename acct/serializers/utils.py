from rest_framework.exceptions import ValidationError


class CreateUpdateRelationMixin:
    """
    Serializer mixin to create or update a reverse
    foreignkey related property on an object.

    In an update action (PUT) only,
    - Create if: id property on relation datum is not present,
                 id property on relation datum does not match
                 any relation object id in DB
    - Update if: object is found based on id
    - Delete if: object is in DB but not part of the relation data.

    e.g
    journal_entry_data = {
        "name": "Entry",
        "note": "test entry",
        "lines": [
            {
                "id": 0,
                "type": "debit,
                "amount": 5000
            },
            {
                "id": 2,
                "type": "credit,
                "amount": 5000
            }
        ]
    }

    In this example, "lines" is the source of truth for all the
    related JournalEntryLine objects for the JournalEntry instance.

    """

    def update_relation(self, field_name, manager, data):
        if data is None:
            return

        relation_serializer = self.fields[field_name]
        relation_ModelClass = relation_serializer.child.Meta.model
        updated_relations = []

        for relation_datum in data:
            assert isinstance(relation_datum, dict)
            related_parent_field = {manager.field.name: manager.instance}
            relation_datum.update(related_parent_field)

            try:
                if relation_datum.get("id") is None:
                    raise relation_ModelClass.DoesNotExist

                relation_object = relation_ModelClass.objects.get(
                    id=relation_datum["id"]
                )
                if (
                    relation_object.__dict__[manager.field.name + "_id"]
                    is not manager.instance.id
                ):
                    raise ValidationError("Invalid relation data.")

                updated_relation_object = relation_serializer.child.update(
                    relation_object, relation_datum
                )
            except relation_ModelClass.DoesNotExist:
                relation_datum.pop("id", None)
                updated_relation_object = relation_serializer.child.create(
                    relation_datum
                )
            updated_relations.append(updated_relation_object)

        if not self.partial:
            updated_relations_ids = [rel.id for rel in updated_relations]
            manager.exclude(id__in=updated_relations_ids).delete()
