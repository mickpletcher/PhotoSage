from photosage.metadata.gps_parser import parse_gps_altitude, parse_gps_coordinate, parse_gps_info, parse_gps_timestamp


def test_parse_gps_coordinate_north_and_west():
    assert round(parse_gps_coordinate((36, 30, 0), "N"), 6) == 36.5
    assert round(parse_gps_coordinate((87, 45, 0), "W"), 6) == -87.75


def test_parse_gps_info_returns_full_payload():
    gps = parse_gps_info(
        {
            "GPSLatitude": (36, 30, 0),
            "GPSLatitudeRef": "N",
            "GPSLongitude": (87, 45, 0),
            "GPSLongitudeRef": "W",
            "GPSAltitude": 150,
            "GPSDateStamp": "2026:05:25",
            "GPSTimeStamp": (12, 15, 30),
        }
    )

    assert gps["latitude"] == 36.5
    assert gps["longitude"] == -87.75
    assert gps["altitude"] == 150
    assert gps["gps_timestamp"].isoformat() == "2026-05-25T12:15:30"


def test_parse_gps_altitude_below_sea_level():
    assert parse_gps_altitude(20, 1) == -20

