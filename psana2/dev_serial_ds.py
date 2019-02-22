"""
from psana.eventbuilder import EventBuilder

views=[]
views.append(memoryview(bytearray(b'abc')))
views.append(memoryview(bytearray(b'def')))
views.append(memoryview(bytearray(b'ghi')))

ev = EventBuilder(views, None)
#ev.testme()
"""
from psana import dgram
from psana.psexp.smdreader_manager import SmdReaderManager
from psana.psexp.eventbuilder_manager import EventBuilderManager
import os, time, glob
import numpy as np
from psana.psexp.packet_footer import PacketFooter
from psana.psexp.event_manager import EventManager
from psana.dgrammanager import DgramManager
from psana.psexp.fuzzyevent_store import FuzzyEventStore

def filter(evt):
    return True

if __name__ == "__main__":
    nfiles = 16
    max_events = 10000
    batch_size = 1000
    os.environ['PS_SMD_N_EVENTS']=str(batch_size)

    smd_files = np.asarray(glob.glob('/reg/d/psdm/xpp/xpptut15/scratch/mona/xtc2/smalldata/*-s*.smd.xtc2'))
    xtc_files = np.asarray(glob.glob('/reg/d/psdm/xpp/xpptut15/scratch/mona/xtc2/*-s*.xtc2'))
    epic_file = '/reg/d/psdm/xpp/xpptut15/scratch/mona/xtc2/data-r0001-epc.xtc2'
    smd_dm = DgramManager(smd_files)
    smd_configs = smd_dm.configs
    dm = DgramManager(xtc_files)
    fuzzy_es = FuzzyEventStore(fuzzy_file=epic_file)

    ev_man = EventManager(smd_configs, dm, filter_fn=0, fuzzy_es=fuzzy_es)
   
    #get smd chunks
    smdr_man = SmdReaderManager(smd_dm.fds, max_events)
    eb_man = EventBuilderManager(smd_configs, batch_size, filter)
    cn_d = 0
    delta_t = []
    for i, chunk in enumerate(smdr_man.chunks()):
        for j, batch in enumerate(eb_man.batches(chunk)):
            st = time.time()
            for k, evt in enumerate(ev_man.events(batch)):
                en = time.time()
                delta_t.append((en - st)*1000)
                st = time.time()

    delta_thres = 200
    delta_t = np.asarray(delta_t) 
    delta_t_sml = delta_t[delta_t < delta_thres]
    delta_t_big = delta_t[delta_t >= delta_thres] / 1000 # unit in seconds
    total_t = np.sum(delta_t)/ 1000 # unit in seconds
    
    print('n_events: %d batch_size: %d mean (ms) %6.4f min %6.4f max %6.4f std %6.4f'%(max_events, batch_size, np.mean(delta_t_sml), np.min(delta_t_sml), np.max(delta_t_sml), np.std(delta_t_sml)))
    
    if len(delta_t_big) > 0:
        print('Batch read (s) mean: %6.4f min: %6.4f max: %6.4f std: %6.4f'%(np.mean(delta_t_big), np.min(delta_t_big), np.max(delta_t_big), np.std(delta_t_big)))
        print('#points > %d ms: %d'%(delta_thres, len(delta_t_big)))
    
    print('Total Elapsed (s): %6.2f Rate (kHz): %6.2f Bandwidth (MB/s): %6.2f'%(total_t, max_events/ (total_t*1000), (737 * nfiles * max_events) / (total_t * 1000000)))