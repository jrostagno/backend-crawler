import unittest

from app.core.text_processing import count_words, tokenize_text


class TestTextProcessing(unittest.TestCase):
    def test_tokenize_filters_stopwords_and_normalizes(self) -> None:
        text = "The Creative life is amazing, and THE camera works with your phone."
        tokens = tokenize_text(text)

        self.assertIn("creative", tokens)
        self.assertIn("camera", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("is", tokens)

    def test_count_words(self) -> None:
        counts = count_words(["camera", "camera", "light"])
        self.assertEqual(counts, {"camera": 2, "light": 1})


if __name__ == "__main__":
    unittest.main()
