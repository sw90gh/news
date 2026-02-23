from scrapers.base import BaseScraper
from scrapers.google_news import GoogleNewsScraper
from scrapers.moef import MoefScraper
from scrapers.mois import MoisScraper
from scrapers.mpm import MpmScraper
from scrapers.law import LawScraper
from scrapers.assembly import AssemblyScraper
from scrapers.korea_kr import KoreaKrScraper

ALL_SCRAPERS = [
    GoogleNewsScraper,
    MoefScraper,
    MoisScraper,
    MpmScraper,
    LawScraper,
    AssemblyScraper,
    KoreaKrScraper,
]
