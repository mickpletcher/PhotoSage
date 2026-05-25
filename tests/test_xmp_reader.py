from photosage.lightroom.xmp_reader import read_xmp, read_xmp_sidecar, sidecar_path_for_image


XMP_TEXT = """<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:xmp="http://ns.adobe.com/xap/1.0/"
           xmlns:lr="http://ns.adobe.com/lightroom/1.0/"
           xmlns:exif="http://ns.adobe.com/exif/1.0/">
    <rdf:Description xmp:Rating="5" xmp:Label="Red" exif:GPSLatitude="36.486" exif:GPSLongitude="-87.839">
      <dc:title><rdf:Alt><rdf:li xml:lang="x-default">Container Home</rdf:li></rdf:Alt></dc:title>
      <dc:description><rdf:Alt><rdf:li xml:lang="x-default">Deck framing at sunset</rdf:li></rdf:Alt></dc:description>
      <dc:subject><rdf:Bag><rdf:li>Construction</rdf:li><rdf:li>Dover TN</rdf:li></rdf:Bag></dc:subject>
      <lr:hierarchicalSubject><rdf:Bag><rdf:li>Projects|Container Home</rdf:li></rdf:Bag></lr:hierarchicalSubject>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def test_read_xmp_extracts_lightroom_fields(tmp_path):
    xmp = tmp_path / "photo.xmp"
    xmp.write_text(XMP_TEXT, encoding="utf-8")

    metadata = read_xmp(xmp)

    assert metadata["title"] == "Container Home"
    assert metadata["caption"] == "Deck framing at sunset"
    assert metadata["keywords"] == ["Construction", "Dover TN"]
    assert metadata["rating"] == 5
    assert metadata["color_label"] == "Red"
    assert metadata["gps_latitude"] == 36.486
    assert metadata["gps_longitude"] == -87.839


def test_read_xmp_sidecar_uses_matching_sidecar(tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"not-an-image")
    sidecar_path_for_image(photo).write_text(XMP_TEXT, encoding="utf-8")

    metadata = read_xmp_sidecar(photo)

    assert metadata["xmp_detected"] is True
    assert metadata["xmp_path"].endswith("photo.xmp")
