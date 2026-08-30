"""
render/page_cache.py
Small LRU cache keyed by (doc_id, page_index, zoom_bucket) so scrolling
back to a recently-seen page at the same zoom doesn't re-render.
Bounded size keeps memory flat regardless of document length.
"""
from collections import OrderedDict


class LRUImageCache:
    def __init__(self, max_items=12):
        self.max_items = max_items
        self._store = OrderedDict()

    @staticmethod
    def make_key(doc_id, page_index, zoom):
        # round zoom to avoid a new cache entry per 1% scroll-zoom jitter
        zoom_bucket = round(zoom, 2)
        return (doc_id, page_index, zoom_bucket)

    def get(self, key):
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def put(self, key, image):
        self._store[key] = image
        self._store.move_to_end(key)
        if len(self._store) > self.max_items:
            self._store.popitem(last=False)

    def invalidate_document(self, doc_id):
        for key in [k for k in self._store if k[0] == doc_id]:
            del self._store[key]

    def clear(self):
        self._store.clear()
