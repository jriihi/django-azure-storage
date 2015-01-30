import os
import traceback
from django.core.management.base import BaseCommand, CommandError, NoArgsCommand
from django.conf import settings
from azure_storage.storage import AzureStorage
from django.core.files import File

class Command(NoArgsCommand):
    help = """Migrate from an existing FileSystemStorage to AzureStorage.
When executing the command "azuremigrate" it will scan for media files in MEDIA_ROOT
and upload all the files to the configured default container."""

    def handle_noargs(self, **options):
        # ensure that project has required configuration
        if not os.path.exists(settings.MEDIA_ROOT):
            raise CommandError('Cannot migrate files from non existing MEDIA_ROOT (%s)' % settings.MEDIA_ROOT)
        if not hasattr(settings, "AZURE_STORAGE"):
            raise CommandError('AZURE_STORAGE setting missing')
	if not settings.AZURE_STORAGE.get("ACCOUNT_NAME", False):
            raise CommandError('AZURE_ACCOUNT_NAME setting missing')
        if not settings.AZURE_STORAGE.get("ACCOUNT_KEY", False):
            raise CommandError('AZURE_ACCOUNT_KEY setting missing')
        if not settings.AZURE_STORAGE.get("CONTAINER", False):
            raise CommandError('AZURE_CONTAINER setting missing')

        # get service interface
        storage = AzureStorage()

        self.stdout.write('Starting migration from "%s" to '
                          'Cloud Storage container "%s\n"' % (settings.MEDIA_ROOT, settings.AZURE_STORAGE['CONTAINER']))

        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                path = os.path.join(root, file)
                blobname = os.path.relpath(path, settings.MEDIA_ROOT).replace('\\', '/')
                self.stdout.write(blobname + "...")
                try:
                    with open(path, 'rb') as f:
                        if storage.save(blobname, File(f)):
                            self.stdout.write("ok\n")
                        else:
                            self.stdout.write("fail\n")
                except Exception as e:
                    self.stdout.write("fail\n")
                    traceback.print_exc()
                    self.stdout.write("aborted migration.\n")
                    return

        self.stdout.write('migration complete')
