#!/usr/bin/python
# -*- coding: utf-8 -*-

# from os import system

import sys
import curses
import traceback
import operator
from subprocess import call

import csv

# choose xmlrpc/ServerProxy to be loaded depending on python    version
if sys.version_info > (3,):
    from xmlrpc.client import ServerProxy
else:
    from xmlrpclib import ServerProxy

# custom configuration
# category: [default directory (custom1), category (custom2), ]
dict = { 'tv':      ['~/done/tv'      , 'TV'      , 'group_1'],
        'toons':    ['~/done/toons'   , 'TOONS'   , 'group_2'],
        'movies':   ['~/done/movies'  , 'MOVIES'  , 'group_2'],
        'software': ['~/done/software', 'SOFTWARE', 'group_3'],
        'muzik':    ['~/done/muzik'   , 'MUZIK'   , 'group_3'],
        'other':    ['~/done/other'   , 'OTHER'   , 'group_3'],
        'seeding':  ['~/done/seeding' , 'SEED'    , 'group_4'],
        }

fmt = [(0, 'hash', 40),
        (1, 'name', 35),
        (2, 'directory', 25), 
        (3, 'custom1', 15),
        (4, 'custom2', 5),
        (5, 'completed', 1),
        (6, 'state', 1),
        (7, 'viewlist', 25)]

width = [tup[2] for tup in fmt]

commands = ['set_custom',
            'set_directory',
            'remove_view',
            'restore_torrent',
            'refresh_list',
        ]

class rtorrent(object):
    """Interface Class to local rtorrent instance"""
    
    def __init__(self, version=3, server_url = 'http://localhost'):
        self.HOME = '/home/matteo'
        self.server_url = server_url
        self.rtorrent = ServerProxy(self.server_url)
        self.hashes = self.rtorrent.download_list()
        self.hashes_num = len(self.hashes)
        self.torrent_list = []

    def __repr__(self):
        """docstring __repr__"""
        return 'server: %s, torrents: %s, selected: %s' % (self.server_url, self.hashes_num, len(self.torrent_list))

    def __str__(self):
        """docstring __str__"""
        return 'server: %s, torrents: %s, selected: %s' % (self.server_url, self.hashes_num, len(self.torrent_list))

    def __getitem__(self, hash):
        """Returns the following torrent attributes as tuple:
            0  hash 
            1  directory directory of the download
            2  name      torrent name
            3  cust1     torrent custom category
            4  cust2     directory to which download will be moved when completed
            5  cust3     unset, torrent custom subcategory
            6  cust4
            7  cust5
            8  complete  C(omplete) or blank
            9  state     X if error else S(tarted), blank otherwise
            10 tied      T(ied) or blank
            11 multi     M(ultifiles) torrent
            12 ignore    I(gnore) command flag or blank
            13 views     views list to which torrent belong (is visible)
        """
        name = self.rtorrent.d.name(hash) #.encode('unicode_escape')
        directory = self.rtorrent.d.directory(hash).replace(self.HOME, '') #.encode('unicode_escape')
        # name = self.rtorrent.d.name(hash)
        # directory = self.rtorrent.d.directory(hash).replace(self.HOME, '')
        cust1 = self.rtorrent.d.custom1(hash)
        cust2 = self.rtorrent.d.custom2(hash)
        cust3 = self.rtorrent.d.custom3(hash)
        cust4 = self.rtorrent.d.custom3(hash)
        cust5 = self.rtorrent.d.custom3(hash)
        state = self.get_state(hash)
        complete = "C" if self.rtorrent.d.complete(hash) else " "
        tied = "T" if 'torrent' in self.rtorrent.d.tied_to_file(hash) else " "
        multi = "M" if self.rtorrent.d.is_multi_file(hash) else " "
        ignore = "I" if self.rtorrent.d.ignore_commands(hash) else " "
        views = ', '.join(self.rtorrent.d.views(hash))
        return (hash, directory, name, cust1, cust2, cust3, cust4, cust5, complete, state, tied, multi, ignore, views)

    def __missing__(self, hash):
        print("Hash missing")

    def refresh(self, progress=0, sample=0):
        """Retrieves full list of rtorrent's hashes
        and calls method /__getitem__/ for each of them
        adding result in list torrent_list
        progress tobedone, for progress bar
        sample=N to get only a sample of N torrents"""
        self.torrent_list = []
        # self.hashes = self.rtorrent.download_list()
        # self.hashes_num = len(self.hashes)
        for i, hash in enumerate(self.hashes):
            if i >= sample and sample != 0: break
            self.torrent_list.append(self[hash])
            # displayProgressBar(mode='progress', position = i)

    def sync_one(self, hash):
        """Update a single element of torrentList""" 
        # get tuple index for the hash passed... and deletes it
        if [i for i, j in enumerate(self.torrent_list) if j[0] == hash]: del self.torrent_list[i] 
        # get new torrent tuple and appends it to torrent_list
        self.torrent_list.append((hash, self[hash]))

    # def formatlist(self):
    #     """Returns a list of tuples each containing hash and a 
    #     fixed-length row of torrents with attributes"""
    #     self.full_downloads=[]
    #     for i_tup in self.torrent_list:
    #         i_tup = tuple(el for i, el in enumerate(i_tup) if i <= 7)
    #         i_lst = [el[:width[i]].ljust(width[i]) for i, el in enumerate(i_tup)]
    #         self.full_downloads.append(' '.join(i_lst))

    def formatted(self):
        """Returns a list of tuples each containing hash and a 
        fixed-length row of torrents with attributes"""
        output_list=[]
        for i_tup in self.torrent_list:
            i_tup = tuple(el for i, el in enumerate(i_tup) if i <= 7)
            i_lst = [el[:width[i]].ljust(width[i]) for i, el in enumerate(i_tup)]
            output_list.append((i_tup[0], ' '.join(i_lst)))
        return output_list

    def formatted2(self):
        """Returns a list of tuples each containing hash and a 
        fixed-length row of torrents with attributes"""
        output_list=[]
        for idx, i_tup in enumerate(self.torrent_list):
            hash = i_tup[0]
            # sovrascrive il contenuto di i_tup per eliminare le colonne superflue <=7
            i_tup = tuple(el for j, el in enumerate(i_tup) if j <= 7)
            i_lst = [el[:width[i]].ljust(width[i]) for i, el in enumerate(i_tup)]
            output_list.append((idx, hash, ' '.join(i_lst)))
        return output_list

    def formatted3(self):
        """Returns a list of tuples each containing hash and a 
        fixed-length row of torrents with attributes"""
        output_list=[]
        for idx, tup in enumerate(self.torrent_list):
            hash = tup[0]
            # padding and truncating: 40, 35, 25, 10, 15, 1, 1, 25
            row = '{0:40.40} {1:35.35} {2:25.25} {3:10.10} {4:15.15} {5} {6} {7:25.25}'.format(*tup)
            output_list.append((idx, hash, row))
        return output_list

    def formatted4(self):
        """Returns a dict containing hash and a 
        fixed-length row of torrents with attributes"""
        output_list=[]
        for idx, tup in enumerate(self.torrent_list):
            hash = tup[0]
            # padding and truncating: 40, 35, 25, 10, 15, 1, 1, 25
            row = '{0:40.40} {1:35.35} {2:25.25} {3:10.10} {4:15.15} {5} {6} {7:25.25}'.format(*tup)
            output_list.append((idx, hash, row))
        return output_list

    def sort(self, *args):
        """Sort torrent_list based on torrents attributes codes"""
        self.torrent_list.sort(key = operator.itemgetter(*args))

    def repair(self, hash):
        pass
        """TO BE DONE - Repair broken link between the actual path of the torrent 
        and the path in rtorrent d.directory property"""


    # CHANGE METADATA
    # change custom1/custom2... values
    def set_custom1(self, hash, cust1):
        """Change custom1 attribute"""
        self.rtorrent.d.set_custom1(hash, cust1)

    def set_custom2(self, hash, cust2):
        """Change custom2 attribute"""
        self.rtorrent.d.set_custom2(hash, cust2)
    
    def set_custom3(self, hash, cust3):
        """Sets custom3 attribute to <cust3> of the given <hash>"""
        self.rtorrent.d.set_custom3(hash, cust3)
    
    def set_custom4(self, hash, cust3):
        """Sets custom3 attribute to <cust3> of the given <hash>"""
        self.rtorrent.d.set_custom3(hash, cust3)
    
    def set_custom5(self, hash, cust3):
        """Sets custom3 attribute to <cust3> of the given <hash>"""
        self.rtorrent.d.set_custom3(hash, cust3)
    
    # add torrent to view
    def set_visible(self, hash, view):
        """add an <hash> to the given <view>"""
        self.rtorrent.view.set_visible(hash, view)
    
    # remove view
    def remove_view(self, hash, view):
        """remove an <hash> from the given <view>"""
        self.rtorrent.d.views.remove(hash, view)
    
    # change torrent download directory to custom1 parameter
    def set_directory(self, hash, cust1):
        """Change directory and custom1 parameter
        changing directory should be set to changed only 
        when you are sure of where the files are"""
        self.rtorrent.d.stop(hash)
        self.rtorrent.d.set_custom1(hash, cust1)
        self.rtorrent.d.directory.set(hash, cust1)
        self.rtorrent.d.start(hash)

    def move_files(self, hash, target_path):
        """move torrent files <to target_path>
        src = RTORRENT.d.base_path(hash)
        tgt = '/'.join([home, 'dome/...somewhere', RTORRENT.d.name(hash)])
        call(["mv", "-u", src, tgt])
        """
        # sposta solo se il torrent è completo
        if self.rtorrent.d.complete(hash):
            source = self.rtorrent.d.base_path(hash)
            target = '/'.join([target_path, self.rtorrent.d.name(hash)])
            call(["mv", "-u", source, target])
        else:
            source =self.rtorrent.d.base_path("~/doing")

    def set_tied(self, hash, filepath):
        self.rtorrent.d.set.tied_to_file(hash, filepath)

    def test_method(self, hash):
        self.__name__ = 'test_method'
        # return self.torrent_list[1]
        self.rtorrent.d.stop(hash)
        return 'hohohooohooh'
        # return self.rtorrent.d.stop

    def get_messages(self):
        # self.__name__ = get_messages
        for t in self.torrent_list:
            message = self.rtorrent.d.message(t[0])
            if message:
                print(t[2], message)

    def get_state(self, hash):
        val = ' '
        if self.has_error(hash): 
            val='X'
        elif self.rtorrent.d.state(hash):
            val='S'
        return val

    def has_error(self, hash):
        message = self.rtorrent.d.message(hash)
        if message == 'Download registered as completed, but hash check returned unfinished chunks.':
            return True

    ### multicall methods
    # d.multicall= group_4, d.start=
    def start_all(self, view):
        """Multicall, starts all torrent of the given <view>"""
        self.rtorrent.d.multicall(view, 'd.start=')
    
    def stop_all(self, view):
        """Multicall, stops all torrents of the given <view>"""
        self.rtorrent.d.multicall(view, 'd.stop=')
    
    def close_all(self, view):
        """Multicall, closes all torrents of the given <view>"""
        self.rtorrent.d.multicall(view, 'd.close=')
    
    def ignore_set(self, view, ic_flag):
        """set <ic_flag> for all torrents of the given <view>
        <ic_flag> must be 0 or 1"""
        if ic_flag in range(2):
            self.rtorrent.d.multicall(view, 'd.ignore_commands.set={0}'.format(ic_flag))
    
    def count_category(self, category):
        """Count torrent in a <category> (custom2)"""
        cnt = sum(category in item[4].strip() for item in rt.torrent_list)
        return str(cnt)

    # compare dirs
    def make_csv(self, csvname):
        """EXPORT """
        table = [['hash', 'multi', 'state', 'name', 'base_filename', 'directory', 'base_path', 'directory_base',
                                        'get_base_filename', 'get_directory', 'get_base_path', 'get_directory_base'],]
        
        for hash in self.rtorrent.download_list():
            multi = "M" if self.rtorrent.d.is_multi_file(hash) else " "
            state = "S" if self.rtorrent.d.get_state(hash) else " "
            
            name = self.rtorrent.d.get_name(hash)

            base_filename = self.rtorrent.d.base_filename(hash)
            directory = self.rtorrent.d.directory(hash)
            base_path = self.rtorrent.d.base_path(hash)
            directory_base = self.rtorrent.d.directory_base(hash)

            get_base_filename = self.rtorrent.d.get_base_filename(hash)
            get_directory = self.rtorrent.d.get_directory(hash)
            get_base_path = self.rtorrent.d.get_base_path(hash)
            get_directory_base = self.rtorrent.d.get_directory_base(hash)

            table.append([hash, multi, state, name, base_filename, directory, base_path, directory_base, 
                                        get_base_filename, get_directory, get_base_path, get_base_filename])

        with open(csvname, 'wb') as csvfile:
            fw = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_ALL)
            for row in table:
                fw.writerow(row)

if __name__ == '__main__':
    rt=rtorrent()
    rt.refresh(sample=10)
    rt.sort(0,)
    print(rt.formatted2())




