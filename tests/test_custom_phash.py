from PIL import Image, ImageDraw
from app.core.custom_crypto.phash import custom_dct_phash, custom_hamming_distance


def test_custom_dct_phash_deterministic():
    """Verify deterministic 16-char hex perceptual hash on identical images."""
    img = Image.new("RGB", (128, 128), color=(30, 40, 60))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 100, 100], fill=(220, 40, 80))

    h1 = custom_dct_phash(img)
    h2 = custom_dct_phash(img)
    assert len(h1) == 16
    assert h1 == h2


def test_custom_dct_phash_similarity_vs_tampering():
    """Verify small compression/resize yields low Hamming distance while structural tampering yields high distance."""
    img = Image.new("RGB", (256, 256), color=(15, 20, 35))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 230, 120], fill=(240, 240, 240))
    draw.ellipse([80, 140, 180, 240], fill=(255, 42, 75))

    # Resize down and back up (benign transcode)
    resized = img.resize((128, 128)).resize((256, 256))
    h_orig = custom_dct_phash(img)
    h_transcoded = custom_dct_phash(resized)
    assert custom_hamming_distance(h_orig, h_transcoded) <= 10

    # Structurally different image
    alt = Image.new("RGB", (256, 256), color=(240, 240, 240))
    draw_alt = ImageDraw.Draw(alt)
    draw_alt.rectangle([10, 130, 240, 240], fill=(10, 10, 10))
    h_alt = custom_dct_phash(alt)
    assert custom_hamming_distance(h_orig, h_alt) > 10


def test_custom_phash_distance_edge_cases():
    h1 = "856a3a3e6bc53a94"
    assert custom_hamming_distance(h1, h1) == 0
    assert custom_hamming_distance(h1, "856a3a3e6bc53a95") == 1
    assert custom_hamming_distance("N/A", h1) == -1
    assert custom_hamming_distance("", h1) == -1
