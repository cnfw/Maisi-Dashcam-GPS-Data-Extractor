import sys
import xml.etree.cElementTree as ET


def main():
    if len(sys.argv) <= 1:
        print("No input file supplied.")
        print("Usage: python3 maisigps.py <file>")
        sys.exit(1)

    # Check that a file was supplied
    print_header(sys.argv[1])

    # Set up root element
    gpx = ET.Element("gpx", {'version': '1.1',
                             'creator': 'Maisi Dashcam GPS Data Extractor - <github url>',
                             'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                             'xmlns': 'http://www.topografix.com/GPX/1/1'})

    # Give the GPX file a name
    ET.SubElement(gpx, "name").text = sys.argv[1]

    # Set up track
    track = ET.SubElement(gpx, "trk")
    ET.SubElement(track, "name").text = sys.argv[1]
    ET.SubElement(track, "number").text = "1"

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
        with (open(sys.argv[1])) as file:
            for i, line in enumerate(file):
                # Every 4 lines starting from the 3rd
                # (Because the file is awkward)
                if i % 4 is 2:
                    make_trkpt(line, track)

    except (IOError, OSError) as e:
        print("There was an issue loading the specified file:")
        print(e)
        sys.exit(1)

    tree = ET.ElementTree(gpx)
    print(sys.argv[1][:-4])
    tree.write(sys.argv[1][:-4] + ".xml")


def make_trkpt(line, track):
    # Ignore invalid GPS points (No GPS fix for example)
    if len(line) != 81:
        return

    gps_time = line[19:38].replace(" ", "T") + ".000Z"

    gps_lat = line[40:48]
    gps_lon = line[51:59]

    # Parse speed and convert to meters per second
    gps_speed = float(line[62:65]) * 0.44704

    # Create elements
    trkpt = ET.SubElement(track, "trkpt", {'lat': gps_lat,
                                           'lon': gps_lon})

    # No elevation data is supplied, so just make it 0
    ET.SubElement(trkpt, "ele").text = "0"

    ET.SubElement(trkpt, "time").text = gps_time

    ET.SubElement(trkpt, "speed").text = str(gps_speed)


def print_header(file_name):
    print("========================================")
    print("Simple GPX Generator using subtitle data")
    print("from Maisi (and similar) dashcams")
    print("========================================")
    print("Title: Maisi GPS Data Extractor")
    print("Version: 0.0")
    print("Author: Christopher Wilkinson")
    print("Date: 12/12/17")
    print("Description: Converts a subtitle file from")
    print("             a Maisi dashcam and outputs")
    print("             it as a more useful GPX file.")
    print("Usage: python3 maisigps <file.srt>")
    print("Python Version: 3")
    print()
    print("Input: " + file_name)
    print("========================================")


if __name__ == '__main__':
    main()
    sys.exit(0)
