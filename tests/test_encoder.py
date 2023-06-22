from mkdocs_puml_mod.encoder import encode


def test_encode(diagram_and_encoded: (str, str)):
    diagram, expected = diagram_and_encoded
    encoded = encode(diagram)

    assert encoded == expected
