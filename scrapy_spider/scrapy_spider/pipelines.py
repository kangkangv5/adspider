# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3
from os import path


from pylib import db
from pydispatch import dispatcher
from scrapy import signals

INSERT_ITEM_SQLITE = '''INSERT INTO AdsProfile
                     (ads_target_url,
                      ads_content_url,
                      ads_present_mode,
                      ads_host,
                      ads_target_domain,
                      ads_host_domain) VALUES(?,?,?,?,?,?)'''
INSERT_ITEM_MYSQL = '''INSERT INTO AdsProfile
                           (ads_target_url,
                            ads_content_url,
                            ads_present_mode,
                            ads_host,
                            ads_target_domain,
                            ads_host_domain)
                            VALUES(%(ads_target_url)s,
                                   %(ads_content_url)s,
                                   %(ads_present_mode)s,
                                   %(ads_host)s,
                                   %(ads_target_domain)s,
                                   %(ads_host_domain)s)'''
CREATE_ADS_PROFILE_TABLE_SQLITE = '''CREATE TABLE IF NOT EXISTS AdsProfile (
                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  ads_target_url TEXT,
                                  ads_content_url TEXT,
                                  ads_present_mode TEXT,
                                  ads_host TEXT,
                                  ads_target_domain TEXT,
                                  ads_host_domain TEXT)'''
CREATE_ADS_PROFILE_TABLE_MYSQL = '''create table if not exists AdsProfile (
                                  id int(16) not null primary key auto_increment,
                                  ads_target_url text,
                                  ads_content_url text,
                                  ads_present_mode text,
                                  ads_host text,
                                  ads_target_domain text,
                                  ads_host_domain text)'''


class SQLiteStorePipeline(object):
    filename = 'ads_profile.sqlite'

    def __init__(self):
        self.conn = None
        dispatcher.connect(self.initialize, signals.engine_started)
        dispatcher.connect(self.finalize, signals.engine_stopped)

    def process_item(self, item, spider):
        self.conn.execute(INSERT_ITEM_SQLITE,
                          (item['ads_target_url'],
                           item['ads_content_url'],
                           item['ads_present_mode'],
                           item['ads_host'],
                           item['ads_target_domain'],
                           item['ads_host_domain']))
        return item

    def initialize(self):
        if path.exists(self.filename):
            self.conn = sqlite3.connect(self.filename)
        else:
            self.conn = self.create_table(self.filename)

    def finalize(self):
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def create_table(self, filename):
        conn = sqlite3.connect(filename)
        conn.execute(CREATE_ADS_PROFILE_TABLE_SQLITE)
        conn.commit()
        return conn


class MySQLStorePipeline(object):

    def __init__(self, dbspec):
        self.conn = None
        self.dbspec = dbspec
        dispatcher.connect(self.initialize, signals.engine_started)
        dispatcher.connect(self.finalize, signals.engine_stopped)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(dbspec=crawler.settings.get('MYSQL_DBSPEC'))

    def process_item(self, item, spider):
        if self.conn is not None:
            self.conn.Execute(INSERT_ITEM_MYSQL,
                              {
                                  'ads_target_url': item['ads_target_url'],
                                  'ads_content_url': item['ads_content_url'],
                                  'ads_present_mode': item['ads_present_mode'],
                                  'ads_host': item['ads_host'],
                                  'ads_target_domain': item['ads_target_domain'],
                                  'ads_host_domain': item['ads_host_domain']
                              })
        return item

    def initialize(self):
        self.conn = db.Connect(self.dbspec)
        if self.conn is not None:
            self.create_table()

    def finalize(self):
        if self.conn is not None:
            self.conn.Close()
            self.conn = None

    def create_table(self):
        self.conn.Execute(CREATE_ADS_PROFILE_TABLE_MYSQL)
