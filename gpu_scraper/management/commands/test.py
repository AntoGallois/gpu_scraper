#! ~/Documents/Django/djenv/bin/python

import datetime
from multiprocessing.connection import wait
import time
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
import urllib3

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Success!'))
        with open("test.log",  "a") as f:
            f.write(f"Executed at {datetime.datetime.now().time()}\n")
        write_in_file()
        


def write_in_file():
    with open("test.log",  "a") as f:
        f.write(f"Start sleeping: {datetime.datetime.now().time()} - ")
        time.sleep(60)
        f.write(f"{datetime.datetime.now().time()}\n")
        