import time
import siuts
from siuts import create_dir
from os import listdir
from os.path import isfile, join
import pickle
import numpy as np
import warnings
import sklearn.utils.validation
import random
import operator

warnings.simplefilter('ignore', sklearn.utils.validation.DataConversionWarning)


def load_pickled_segments_from_file(filename, label, rec_id):
    with open(filename, 'rb') as f:
        segments = pickle.load(f)
    segments_count = len(segments)

    if segments_count == 0:
        return np.empty([0]), np.empty([0]), np.empty([0])
    labels = [label] * segments_count
    rec_ids = [rec_id] * segments_count
    return segments, labels, rec_ids


def join_segments(selected_recordings, segments_dir, data_filepath, labels_filepath, rec_ids_filepath):
    selected_recordings_count = len(selected_recordings)

    all_segments = []
    all_labels = []
    all_rec_Ids = []
    segments_count = {}
    file_count = {}

    if not isfile(data_filepath):
        for counter, rec in enumerate(selected_recordings):
            fname = rec.get_filename()
            label = rec.label
            rec_id = rec.id
            rec_segments, labels, rec_ids = load_pickled_segments_from_file(segments_dir + fname + ".pickle", label,
                                                                            rec_id)
            if (len(rec_segments) > 0 and len(labels) > 0):
                processed_segments = siuts.scale_segments(rec_segments)
                all_segments = all_segments + processed_segments
                all_labels = all_labels + labels
                all_rec_Ids = all_rec_Ids + rec_ids

                specimen = rec.get_name()
                if specimen in segments_count:
                    segments_count[specimen] = segments_count[specimen] + len(processed_segments)
                    file_count[specimen] = file_count[specimen] + 1
                else:
                    segments_count[specimen] = len(processed_segments)
                    file_count[specimen] = 1
            if counter % 100 == 0:
                print "{0}/{1}".format(counter, selected_recordings_count)

        with open(data_filepath, 'wb') as f:
            pickle.dump(np.array(all_segments), f, protocol=-1)

        with open(labels_filepath, 'wb') as f:
            pickle.dump(np.array(all_labels), f, protocol=-1)

        with open(rec_ids_filepath, 'wb') as f:
            pickle.dump(np.array(all_rec_Ids), f, protocol=-1)
        print "File count: " + str(file_count)
        print
        print "Segments count: " + str(segments_count)


# count segments for each recording in testing data 
with open(siuts.testing_recordings_path, "rb") as f:
    plutof_recordings = pickle.load(f)

for rec in plutof_recordings:
    segments_path = siuts.testing_segments_dir + rec.get_filename() + ".pickle"
    if isfile(segments_path):
        with open(segments_path, "rb") as f:
            rec.segments_count = len(pickle.load(f))

# separate testing and validation dataset
valid_recordings = []
test_recordings = []
segments_count = 0
for specimen in siuts.species_list:
    recordings = sorted([x for x in plutof_recordings if x.get_name() == specimen and x.segments_count >= 2],
                        key=operator.attrgetter('segments_count'))
    recordings.reverse()
    sp_valid_recordings = []
    sp_test_recordings = []
    sp_valid_segments_count = 0
    sp_test_segments_count = 0
    for rec in recordings:
        segments_count += rec.segments_count
        if sp_valid_segments_count < sp_test_segments_count:
            sp_valid_recordings.append(rec)
            sp_valid_segments_count += rec.segments_count
        else:
            sp_test_recordings.append(rec)
            sp_test_segments_count += rec.segments_count

    valid_recordings = valid_recordings + sp_valid_recordings
    test_recordings = test_recordings + sp_test_recordings

siuts.create_dir(create_dir(siuts.dataset_dir))

training_segments_dir = siuts.training_segments_dir
testing_segments_dir = siuts.testing_segments_dir

start = time.time()
print "Starting to join testing segments"
print
plutof_filenames = [x.split(".")[0] for x in listdir(testing_segments_dir) if isfile(join(testing_segments_dir, x))]
selected_testing_recordings = [x for x in test_recordings if x.get_filename() in plutof_filenames]

join_segments(selected_testing_recordings, testing_segments_dir, siuts.testing_data_filepath,
              siuts.testing_labels_filepath, siuts.testing_rec_ids_filepath)
print
print "Joining testing segments took {0} seconds".format(time.time() - start)
print

start = time.time()
print
print "Starting to join validation segments"

selected_validation_recordings = [x for x in valid_recordings if x.get_filename() in plutof_filenames]

join_segments(selected_validation_recordings, testing_segments_dir, siuts.validation_data_filepath,
              siuts.validation_labels_filepath, siuts.validation_rec_ids_filepath)
print
print "Joining validation segments took {0} seconds".format(time.time() - start)
print

start = time.time()
max_segments = 0
species_segments_count = {}
species_files_count = {}

print
print "Finding species from training set which has the maximum number of segments"
train_filenames = [x.split(".")[0] for x in listdir(training_segments_dir) if isfile(join(training_segments_dir, x))]
species = siuts.species_list
with open(siuts.training_recordings_path, "rb") as f:
    training_recordings = pickle.load(f)
for specimen in species:
    specimen_files = [x for x in training_recordings if
                      x.get_name() == specimen and x.get_filename() in train_filenames]
    species_files_count[specimen] = len(specimen_files)
    for rec in specimen_files:
        fname = rec.get_filename()
        with open(siuts.training_segments_dir + fname + ".pickle", 'rb') as f:
            segs = pickle.load(f)
        if specimen in species_segments_count:
            species_segments_count[specimen] += len(segs)
        else:
            species_segments_count[specimen] = len(segs)
    if species_segments_count[specimen] > max_segments:
        max_segments = species_segments_count[specimen]
print "Species files count"
print species_files_count
print

print "Species segments count:"
print species_segments_count
print

print "Max segments for species: " + str(max_segments)
print

max_segments_in_file = siuts.samples_in_file

for specimen in species:
    print ""
    print "Joining training segments for {}".format(specimen)
    specimen_files = [x for x in training_recordings if
                      x.get_name() == specimen and x.get_filename() in train_filenames]
    specimen_files_count = len(specimen_files)

    all_segments = np.empty
    all_labels = []
    all_rec_ids = []

    filepath_prefix = "{0}{1}_".format(siuts.dataset_dir, specimen)
    labels_fname = filepath_prefix + "labels.pickle"
    rec_Ids_fname = filepath_prefix + "rec_ids.pickle"

    if not (isfile(labels_fname) and isfile(rec_Ids_fname)):
        for counter, rec in enumerate(specimen_files):
            fname = rec.get_filename()
            label = rec.label
            rec_id = rec.id
            rec_segments, labels, rec_ids = load_pickled_segments_from_file(
                siuts.training_segments_dir + fname + ".pickle", label, rec_id)
            if len(rec_segments) > 0 and len(labels) > 0:
                processed_segments = np.array(siuts.scale_segments(rec_segments))

                all_labels = all_labels + labels
                all_rec_ids = all_rec_ids + rec_ids
                if counter == 0:
                    all_segments = processed_segments
                else:
                    all_segments = np.vstack((all_segments, processed_segments))

            if counter % 100 == 0:
                print "{0}/{1}".format(counter, specimen_files_count)

        del rec_segments
        del processed_segments
        print "Saving joined files to disk"

        random.shuffle(all_segments)
        nr_samples = len(all_segments)
        if (nr_samples < max_segments):
            data_to_append = np.copy(all_segments)
            for j in range(int(np.floor(max_segments / nr_samples)) - 1):
                all_segments = np.concatenate((all_segments, data_to_append))
            all_segments = np.concatenate((all_segments, data_to_append[:(max_segments - len(all_segments))]))
        nr_of_files = int(np.ceil(float(max_segments) / siuts.samples_in_file))
        for i in range(nr_of_files):
            with open("{0}/{1}-training_{2}.pickle".format(siuts.dataset_dir, specimen, i), 'wb') as f:
                pickle.dump(all_segments[i * siuts.samples_in_file:(i + 1) * siuts.samples_in_file], f, protocol=-1)
        print specimen + " segments saved"

        with open(labels_fname, 'wb') as f:
            pickle.dump(np.array(all_labels), f, protocol=-1)

        with open(rec_Ids_fname, 'wb') as f:
            pickle.dump(np.array(all_rec_ids), f, protocol=-1)

print "Joining training segments took {0} seconds".format(time.time() - start)