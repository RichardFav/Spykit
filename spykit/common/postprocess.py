# module import
import os
import struct
import numpy as np
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QObject

# ----------------------------------------------------------------------------------------------------------------------

"""
    PostMemMap:  post-processing data memory map 
"""

class PostMemMap(QObject):
    # pyqtsignal functions
    progress_fcn = pyqtSignal(int, int)

    # dimension fields
    n_dim_para = 7

    def __init__(self):
        super(PostMemMap, self).__init__()

        # field initialsiation
        self.mmap_file = None

    def set_mmap_file(self, mmap_file_new):

        # sets the input arguments
        self.mmap_file = mmap_file_new.replace('\\', '/')

    def write_mem_map(self, bc_data):

        # field retrieval
        p_fcn = bc_data.get_para_value

        # array dimensions
        n_unit = int(bc_data.array_dim['nUnit'])
        n_pts = int(bc_data.array_dim['nPts'])
        n_ch = int(bc_data.array_dim['nCh'])
        n_ch_full = int(bc_data.array_dim['nChFull'])
        n_spike = int(bc_data.array_dim['nSpike'])
        n_qual_met = int(bc_data.array_dim['nQualMet'])
        n_hdr_max = int(bc_data.array_dim['nHdrMax'])

        # structure dtype
        dt = self.get_dtype(n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max)
        m_map = np.memmap(self.mmap_file, dtype=dt, mode='w+', shape=(1,))

        # sets the memory map fields
        n_fld = len(dt.names)
        for i_fld, dt_n in enumerate(dt.names):
            # progress update
            self.progress_fcn.emit(i_fld, n_fld)

            # parameter field value
            p_val_new = p_fcn(dt_n)
            if p_val_new is None:
                # case is a local variable
                m_map[dt_n] = eval(dt_n)

            else:
                # case is a bombcell data field
                m_map[dt_n] = p_val_new

        # flushes data to disk
        m_map.flush()
        del m_map

    def read_mem_map(self):

        with open(self.mmap_file, 'rb') as f:
            # reads the first n_dim_para
            data_bytes = f.read(4 * self.n_dim_para)
            dim_vals = struct.unpack(f'{self.n_dim_para}i', data_bytes)

            # sets up the memory map data type
            n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max = self.get_array_dim()
            dt = self.get_dtype(n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max)

            # returns the memory map
            return np.memmap(self.mmap_file, dtype=dt, mode='r', shape=(1,))

    def get_array_dim(self):

        with open(self.mmap_file, 'rb') as f:
            # reads the first n_dim_para
            data_bytes = f.read(4 * self.n_dim_para)
            return struct.unpack(f'{self.n_dim_para}i', data_bytes)

    def get_dtype(self, n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max):

        dt_type = np.dtype([
            # case is array dimensions
            ('n_unit', 'i4'),
            ('n_pts', 'i4'),
            ('n_ch', 'i4'),
            ('n_ch_full', 'i4'),
            ('n_spike', 'i4'),
            ('n_qual_met', 'i4'),
            ('n_hdr_max', 'i4'),

            # case is ephys data
            ('i_spike', 'f4', (n_spike, 1)),
            ('spk_cluster', 'i4', (n_spike, 1)),
            ('t_wform', 'f4', (n_unit, n_pts, n_ch)),
            ('t_amp', 'f4', (n_spike, 1)),
            ('ch_pos', 'f4', (n_ch, 2)),
            ('s_rate', 'i4'),
            ('T_wform', 'f4', (1, n_pts)),
            ('t_spike', 'f4', (n_spike, 1)),

            # case is quality metrics
            ('q_hdr', f'U{n_hdr_max}', (1, n_qual_met)),
            ('q_met', 'f4', (n_unit, n_qual_met)),

            # case is raw waveforms
            ('avg_sig', 'f4', (n_unit, n_ch_full, n_pts)),
            ('pk_ch', 'f4', (n_unit, 1)),

            # case is miscellaneous field
            ('unit_type', 'i4', (n_unit, 1)),
            ('t_unique', 'i4', (n_unit, 1)),
        ])

        return dt_type