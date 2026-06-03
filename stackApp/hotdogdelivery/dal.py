"""Data Access Layer (DAL) for orders.

This module provides a thin abstraction over either Firestore (when
Firebase credentials are available) or a simple in-memory fallback store
used for local development and testing. It tries to keep the API stable
so the rest of the application doesn't need to know which backend is
being used.

The in-memory store is intentionally lightweight and not meant for
production use.

Admin users are stored in a Firestore `admins` collection. Each document
must contain a `uid` field matching the Firebase Auth UID.  For the
in-memory fallback, call add_admin_uid(uid) to grant admin access.
"""

import os
import logging
import threading
from copy import deepcopy

logger = logging.getLogger(__name__)

_initialized = False
_use_firestore = False
_client = None
_lock = threading.Lock()

# Simple in-memory fallback store so the app still runs if Firebase isn't configured
_in_memory_store = []
_admin_uids = set()  # in-memory admin UID store for the fallback backend
_reviews_store = []  # in-memory reviews: [{orderId, userId, reaction}]


def init_app():
    """Initialize Firebase/Firestore client if credentials are available.

    - If the environment variable FIREBASE_CREDENTIALS is set to a service
      account JSON file path, it will attempt to initialize using that.
    - If initialization fails for any reason, the DAL will fall back to an
      in-memory store so the existing app remains functional for development.
    """
    global _initialized, _use_firestore, _client
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        try:
            # Import here to avoid a hard dependency unless init_app is used
            import firebase_admin
            from firebase_admin import credentials, firestore

            cred_path = os.environ.get('FIREBASE_CREDENTIALS')
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # try default app (e.g., when running in GCP with ADC)
                firebase_admin.initialize_app()

            _client = firestore.client()
            _use_firestore = True
            logger.info('Firebase Admin SDK initialised — Firestore backend active (project: csc270-stackapp-aa78c)')
        except Exception as exc:
            _use_firestore = False
            _client = None
            logger.warning('Firebase Admin SDK failed to initialise — using in-memory fallback (%s)', exc)
        _initialized = True


def is_firebase_ready():
    """Return True if the Firebase Admin SDK is initialized and usable."""
    return _initialized and _use_firestore and _client is not None


def _doc_to_order(doc):
    data = doc.to_dict()
    return {
        'id': int(data.get('id')) if data.get('id') is not None else None,
        'userId': data.get('userId', ''),
        'customerName': data.get('customerName', ''),
        'hotdogName': data.get('hotdogName', ''),
        'unitPrice': float(data.get('unitPrice', 0.0)),
        'quantity': int(data.get('quantity', 1)),
        'notes': data.get('notes', ''),
        'status': data.get('status', 'pending'),
    }


def get_all_orders():
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.stream()
        return [_doc_to_order(d) for d in docs]

    # fallback
    return deepcopy(_in_memory_store)


def get_orders_by_user(user_id):
    """Return only the orders that belong to the given Firebase UID."""
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.where('userId', '==', user_id).stream()
        return [_doc_to_order(d) for d in docs]

    # fallback
    return deepcopy([o for o in _in_memory_store if o.get('userId') == user_id])


def is_admin(uid):
    """Return True if the given Firebase UID belongs to an admin.

    Firestore: checks the `admins` collection for a document with uid == uid.
    In-memory: checks the _admin_uids set (populated via add_admin_uid).
    """
    init_app()
    if _use_firestore and _client is not None:
        docs = _client.collection('admins').where('uid', '==', uid).limit(1).stream()
        for _ in docs:
            return True
        return False

    return uid in _admin_uids


def add_admin_uid(uid):
    """Grant admin access for the in-memory fallback (dev/test only)."""
    _admin_uids.add(uid)


def _find_doc_snapshot_by_id(order_id):
    """Return a Firestore document snapshot-like object for the given id.

    When using Firestore this returns the snapshot returned by the
    query stream (or None when not found). When the in-memory fallback is
    active a lightweight object with a `to_dict()` method is returned so
    the rest of the module can use the same _doc_to_order() conversion.
    """
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        # query by numeric 'id' field
        query = coll.where('id', '==', int(order_id)).limit(1).stream()
        for doc in query:
            return doc
        return None

    # in-memory fallback
    for idx, item in enumerate(_in_memory_store):
        if item.get('id') == int(order_id):
            # Construct a lightweight doc-like object compatible with
            # the Firestore snapshot API used elsewhere in this module.
            class _Doc:
                def __init__(self, data):
                    self._data = data

                def to_dict(self):
                    return self._data

                @property
                def reference(self):
                    # Keep an attribute for callers that expect a reference
                    # object (used in update/delete paths); return None
                    # for the in-memory fallback.
                    return None

            return _Doc(_in_memory_store[idx])

    return None


def get_order_by_id(order_id):
    doc = _find_doc_snapshot_by_id(order_id)
    if not doc:
        return None
    return _doc_to_order(doc)


def create_order(order_data):
    """Create an order in Firestore (or in-memory fallback).

    The DAL will assign a numeric incremental `id` field so the rest of the
    app can continue using integer IDs.
    """
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        # compute next id
        docs = coll.order_by('id', direction='DESCENDING').limit(1).stream()
        next_id = 1
        for d in docs:
            ddata = d.to_dict()
            try:
                next_id = int(ddata.get('id', 0)) + 1
            except Exception:
                next_id = 1
        payload = dict(order_data)
        payload['id'] = int(next_id)
        coll.add(payload)
        return get_order_by_id(next_id)

    # in-memory fallback
    if _in_memory_store:
        max_id = max((item.get('id', 0) for item in _in_memory_store), default=0)
        next_id = max_id + 1
    else:
        next_id = 1
    payload = dict(order_data)
    payload['id'] = next_id
    _in_memory_store.append(payload)
    return deepcopy(payload)


def update_order(order_id, updates):
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.where('id', '==', int(order_id)).limit(1).stream()
        for d in docs:
            d.reference.update(updates)
            return get_order_by_id(order_id)
        return None

    # in-memory fallback
    for idx, item in enumerate(_in_memory_store):
        if item.get('id') == int(order_id):
            for k, v in updates.items():
                item[k] = v
            return deepcopy(item)
    return None


def delete_order(order_id):
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.where('id', '==', int(order_id)).limit(1).stream()
        for d in docs:
            d.reference.delete()
            return True
        return False

    # in-memory fallback
    for item in list(_in_memory_store):
        if item.get('id') == int(order_id):
            _in_memory_store.remove(item)
            return True
    return False


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

def get_completed_orders():
    """Return all orders with status 'completed'."""
    init_app()
    if _use_firestore and _client is not None:
        docs = _client.collection('orders').where('status', '==', 'completed').stream()
        return [_doc_to_order(d) for d in docs]
    return deepcopy([o for o in _in_memory_store if o.get('status') == 'completed'])


def get_reviews_for_order(order_id):
    """Return list of {userId, reaction} dicts for the given order."""
    init_app()
    if _use_firestore and _client is not None:
        docs = _client.collection('reviews').where('orderId', '==', int(order_id)).stream()
        return [{'userId': d.to_dict().get('userId'), 'reaction': d.to_dict().get('reaction')} for d in docs]
    return deepcopy([
        {'userId': r['userId'], 'reaction': r['reaction']}
        for r in _reviews_store if r.get('orderId') == int(order_id)
    ])


def get_user_review(order_id, user_id):
    """Return the user's reaction ('like'/'dislike') for an order, or None."""
    init_app()
    if _use_firestore and _client is not None:
        docs = (
            _client.collection('reviews')
            .where('orderId', '==', int(order_id))
            .where('userId', '==', user_id)
            .limit(1)
            .stream()
        )
        for d in docs:
            return d.to_dict().get('reaction')
        return None
    for r in _reviews_store:
        if r.get('orderId') == int(order_id) and r.get('userId') == user_id:
            return r.get('reaction')
    return None


def upsert_review(order_id, user_id, reaction):
    """Add or update a user's like/dislike on an order."""
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('reviews')
        docs = list(
            coll.where('orderId', '==', int(order_id))
            .where('userId', '==', user_id)
            .limit(1)
            .stream()
        )
        if docs:
            docs[0].reference.update({'reaction': reaction})
        else:
            coll.add({'orderId': int(order_id), 'userId': user_id, 'reaction': reaction})
        return True
    # in-memory fallback
    for r in _reviews_store:
        if r.get('orderId') == int(order_id) and r.get('userId') == user_id:
            r['reaction'] = reaction
            return True
    _reviews_store.append({'orderId': int(order_id), 'userId': user_id, 'reaction': reaction})
    return True
