from scrapers.base import BaseScraper
from scrapers.naver_news import NaverNewsScraper
from scrapers.moef import MoefScraper
from scrapers.mois import MoisScraper
from scrapers.mpm import MpmScraper
from scrapers.law import LawScraper
from scrapers.assembly import AssemblyScraper

ALL_SCRAPERS = [
    NaverNewsScraper,
    MoefScraper,
    MoisScraper,
    MpmScraper,
    LawScraper,
    AssemblyScraper,
]
