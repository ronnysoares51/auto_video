import unittest
from selector import select, product_key, rank


def item(name, views, sales=0):
    return {
        "name": name,
        "product_url": f"https://example.com/{name}",
        "image_urls": ["https://example.com/photo.jpg"],
        "image_rights_confirmed": True,
        "views": views,
        "sales": sales,
    }


class SelectionTests(unittest.TestCase):
    def test_ranks_highest_first(self):
        values = select([item("a", 10), item("b", 200000)], {}, 2)
        self.assertEqual(values[0]["name"], "b")

    def test_skips_delivered(self):
        first = item("a", 1000)
        self.assertEqual(select([first], {product_key(first): {}}, 3), [])

    def test_skips_unauthorized_and_duplicates(self):
        a = item("a", 100)
        b = item("b", 200)
        b["image_rights_confirmed"] = False
        self.assertEqual(len(select([a, a, b], {}, 3)), 1)

    def test_real_metrics_not_required(self):
        self.assertEqual(rank(item("a", 0)), 0.0)


if __name__ == "__main__":
    unittest.main()
