import siuts
from siuts import create_dir
import time
import pickle
import os
import numpy as np



def segment_wavs(recordings_file, segments_dir, wavs_dir):
    create_dir(segments_dir)
    with open(recordings_file, "rb") as f:
        recordings = pickle.load(f)
    recordings_count = len(recordings)
    for counter, rec in enumerate(recordings):
        fname = rec.get_filename()
        pickle_path = segments_dir + fname + ".pickle"
        if not os.path.isfile(pickle_path):
            wav_path = "{0}{1}.wav".format(wavs_dir, fname)
            if os.path.isfile(wav_path):
                segments = segment_wav(wav_path)
                if len(segments) > 0:
                    with open(segments_dir + fname + ".pickle", 'wb') as f:
                        pickle.dump(segments, f, protocol=-1)
        if counter % 100 == 0:
            print "{0}/{1} file segmented".format(counter, recordings_count)





print "Starting training data segmentation"
start = time.time()
segment_wavs(siuts.xeno_metadata_path, siuts.xeno_segments_dir, siuts.xeno_wavs_dir)
print "Training data segmentation took {0} seconds".format(time.time() - start)

print "Starting testing segmentation"
start = time.time()
segment_wavs(siuts.plutof_metadata_path, siuts.plutof_segments_dir, siuts.plutof_wavs_dir)
print "Testing data segmentation took {0} seconds".format(time.time() - start)
