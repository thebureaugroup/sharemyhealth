from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

__author__ = "Alan Viars"

groups = ["ApplicationDeveloper", ]


def create_groups():

    created_groups = []
    for group in groups:
        g, created = Group.objects.get_or_create(name=group)
        created_groups.append(g)

        # Allow person to register an app
        if group == "ApplicationDeveloper":
            # Add permissions to group
            content_type = ContentType.objects.get(
                app_label='oauth2_provider', model='application')
            add = Permission.objects.get(codename='add_application',
                                         content_type=content_type)
            change = Permission.objects.get(codename='change_application',
                                            content_type=content_type)
            delete = Permission.objects.get(codename='delete_application',
                                            content_type=content_type)
            view = Permission.objects.get(codename='view_application',
                                          content_type=content_type)
            g.permissions.add(add, change, delete, view)
            g.save()

    return dict(zip(groups, created_groups))


class Command(BaseCommand):
    help = 'Create default groups %s ' % (groups)

    def handle(self, *args, **options):

        g = create_groups()
        print("Groups %s created if they did not already exist." % (g))
