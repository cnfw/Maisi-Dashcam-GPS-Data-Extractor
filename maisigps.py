import sys
from os import path, listdir, makedirs
from subprocess import call
import argparse
import xml.etree.cElementTree as ET

"""
A work in progress
"""


def main():
    parser = setup_parser()

    values = parser.parse_args()
    file_path = values.path

    # If path is a file, go work with it
    if path.isfile(file_path):
        extract_srt_file(file_path, path.dirname(file_path))
        root = setup_gpx_root(file_path[:-4] + '.srt')
        add_track_to_root(root, file_path[:-4] + '.srt')
        generate_tree_and_write_file(root, file_path[:-4] + '.srt')

    elif path.isdir(file_path):
        srt_directory = file_path + '\\' + 'srt'
        if not path.exists(srt_directory):
            makedirs(srt_directory)
        gpx_directory = file_path + '\\' + 'gpx'
        if not path.exists(gpx_directory):
            makedirs(gpx_directory)

        for file in listdir(file_path):
            print('\rExtracting data from videos.', end='  ')
            extract_srt_file(file_path + '\\' + file, srt_directory)
        print('\rFinished extracting data from videos.')
        # Do these separately in case of any failures in the extraction process

        root = setup_gpx_root(file_path + '_join.gpx')
        join_count = 1
        for file in listdir(srt_directory):
            print('\rCreating GPX files.', end='  ')
            if not values.join:
                root = setup_gpx_root(srt_directory + '\\' + file)
            add_track_to_root(root, srt_directory + '\\' + file, track_number=join_count)
            if values.join:
                join_count += 1
                continue
            generate_tree_and_write_file(root, srt_directory + '\\' + file, gpx_directory)

        if values.join:
            generate_tree_and_write_file(root, file_path + '_join.gpx', gpx_directory)

        print('\rGPX files created in ' + gpx_directory)
    else:
        print('Invalid file or directory supplied. Check that the file or directory exists.')


def extract_srt_file(file_path, output_dir):
    call(['ffmpeg', '-i', file_path, '-map', '0:s:0', output_dir + '\\' + path.basename(file_path)[:-4] + '.srt',
          '-loglevel', 'quiet'])


def setup_gpx_root(file_path):

    # Set up root element
    gpx = ET.Element("gpx", {'version': '1.1',
                             'creator': 'Maisi Dashcam GPS Data Extractor - '
                                        'https://github.com/cw1998/MaisiDashcamGPSDataExtractor',
                             'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                             'xmlns': 'http://www.topografix.com/GPX/1/1'})

    # Give the GPX file a name
    ET.SubElement(gpx, "name").text = path.basename(file_path)
    return gpx


def add_track_to_root(root, file_path, track_number=1):
    track = ET.SubElement(root, "trk")
    ET.SubElement(track, "name").text = path.basename(file_path)
    ET.SubElement(track, "number").text = str(track_number)

    """
    Maisi Dashcam SRT structure
    File structure:
     1 Blank Line
     2 Point number
     3 Video Time Stamp
     4 The data
    """

    # Get input from the file passed in
    try:
        with open(file_path) as file:
            for i, line in enumerate(file):
                # Every 4 lines starting from the 3rd
                # (Because the file is awkward)
                if i % 4 is 2:
                    data = get_data_from_line(line)
                    if data is False:
                        continue
                    make_trkpt(data, track)

    except (IOError, OSError) as e:
        print("There was an issue loading the specified file:")
        print(e)
        return


def generate_tree_and_write_file(root, file_path, output_dir=None):
    tree = ET.ElementTree(root)
    output_name = file_path if output_dir is None else output_dir + '\\' + path.basename(file_path)
    tree.write(output_name[:-4] + ".gpx")


def get_data_from_line(input_line):
    data = input_line.split('}', 1)[-1].split('_', 1)[0].strip(' ').split(':', 2)[-1]

    # Check line length - valid lines should have 46 characters
    # 19 for date, 10 for lat, 10 for lon, 4 for speed, plus 3 separating hyphens
    if len(data) != 46:
        return False

    # gps_speed in GPX files are stored in meters per second, so this needs converted.
    return {'gps_time': data[:19].replace(" ", "T") + ".000Z",
            'gps_lat': data.split('-', 3)[-1][1:10],
            'gps_lon': data.split('-', 4)[-1][1:10],
            'gps_speed': float(data.split('S', 2)[-1]) * 0.44704}


def make_trkpt(data, track):
    trkpt = ET.SubElement(track, "trkpt", {'lat': data['gps_lat'],
                                           'lon': data['gps_lon']})

    ET.SubElement(trkpt, "ele").text = "0"
    ET.SubElement(trkpt, "time").text = data['gps_time']
    ET.SubElement(trkpt, "speed").text = str(data['gps_speed'])

    # No return necessary as the sub elements are added directly to the root tree supplied.


def print_header():
    print("========================================")
    print("Simple GPX Generator using subtitle data")
    print("from Maisi (and similar) dashcams")
    print("========================================")
    print("Title: Maisi GPS Data Extractor")
    print("Version: 0.2")
    print("Author: Christopher Wilkinson")
    print("Date: 12/12/17")
    print("Description: Extracts GPS data from")
    print("             a Maisi dashcam and outputs")
    print("             it as a more useful GPX file.")
    print("Usage: See -h or --help")
    print("Python Version: 3")
    print("========================================")


def setup_parser():
    parser = argparse.ArgumentParser(description='Extract GPS data from Maisi dashcam footage files.\n'
                                                 'By default, if a directory is supplied, a GPX file will be created '
                                                 'for each SRT file in that directory')

    parser.add_argument('path', help='File path or a directory of files for bulk extraction')
    parser.add_argument('-o', '--output', dest='output',
                        help='Custom output directory (Defaults to same directory as source file)')
    parser.add_argument('-j', '--join', action='store_true', default=False, dest='join',
                        help='Creates one large GPX file from a directory of source files')

    return parser


if __name__ == '__main__':
    print_header()
    main()
    sys.exit(0)
