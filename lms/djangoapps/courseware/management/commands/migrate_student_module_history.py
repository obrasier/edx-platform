# pylint: disable=missing-docstring

from datetime import timedelta
from textwrap import dedent
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from courseware.models import StudentModuleHistory, StudentModuleHistoryArchive


class Command(BaseCommand):
    """
    Command to migrate all data from StudentModuleHistoryArchive into StudentModuleHistory.
    """
    help = dedent(__doc__).strip()


    def handle(self, *args, **options):
        try:
            max_id = StudentModuleHistory.objects.all().order_by('id')[0].id
        except IndexError:
            self.stdout.write("No entries found in StudentModuleHistory, aborting migration.\n")
            return

        self.migrate_range(0, max_id)


    @transaction.commit_manually
    def migrate_range(self, min_id, max_id, window=1000):
        self.stdout.write("Migrating StudentModuleHistoryArchive entries {}-{}\n".format(max_id, min_id))
        start_time = time.time()

        archive_entries = (
            StudentModuleHistoryArchive.objects
            .select_related('student_module__student')
            .order_by('-id')
        )


        real_max_id = None
        count = 0
        current_max_id = max_id

        try:
            #what about the entries min_id < x < window when (max_id - min_id) % window != 0?
            while current_max_id > min_id:
                #this could overlap into the range below
                entries = archive_entries.filter(id__lt=current_max_id, id__gte=current_max_id - window)

                new_entries = [StudentModuleHistory.from_archive(entry) for entry in entries]

                StudentModuleHistory.objects.bulk_create(new_entries)
                count += len(entries)

                if entries:     #when would this be false?
                    transaction.commit()
                    duration = time.time() - start_time

                    self.stdout.write("Migrated StudentModuleHistoryArchive {}-{} to StudentModuleHistory\n".format(entries[0].id, entries[-1].id))
                    self.stdout.write("Migrating {} entries per second. {} seconds remaining...\n".format(
                        (count + 1) / duration,     #why count+1?
                        timedelta(seconds=(entries[-1].id / (count + 1)) * duration),  #as above
                    ))

                current_max_id -= window
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()
            if real_max_id is None:
                real_max_id = entries[0]

            if entries:
                self.stdout.write("Migrated StudentModuleHistoryArchive {}-{} to StudentModuleHistory\n".format(real_max_id, entries[-1].id))
                self.stdout.write("Migration complete\n")
            else:
                self.stdout.write("No migration needed\n")