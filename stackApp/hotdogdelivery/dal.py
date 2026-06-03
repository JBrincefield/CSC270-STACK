"""Data Access Layer (DAL) for orders.

This module provides a thin abstraction over either Firestore (when
Firebase credentials are available) or a simple in-memory fallback store
used for local development and testing. It tries to keep the API stable
so the rest of the application doesn't need to know which backend is
being used.

The in-memory store is intentionally lightweight and not meant for
production use.
"""

import os
import threading
from copy import deepcopy
from datetime import datetime, timezone

_initialized = False
_use_firestore = False
_client = None
_lock = threading.Lock()

# Simple in-memory fallback store so the app still runs if Firebase isn't configured
_in_memory_store = []


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

            # Firestore uses gRPC which hangs indefinitely on auth failures.
            # Probe credentials now with a fast REST call; if the service
            # account key is invalid the RefreshError surfaces here in ~500ms
            # instead of on every subsequent Firestore query.
            import google.auth.exceptions
            from firebase_admin import auth as _fb_auth
            try:
                _fb_auth.get_user('__cred_check__')
            except google.auth.exceptions.RefreshError:
                raise  # broken credentials — skip Firestore
            except Exception:
                pass  # UserNotFoundError etc. — credentials are fine

            _client = firestore.client()
            _use_firestore = True
        except Exception:
            # If anything goes wrong, keep using the in-memory store
            _use_firestore = False
            _client = None
        _initialized = True


def _doc_to_order(doc):
    data = doc.to_dict()
    return {
        'id': int(data.get('id')) if data.get('id') is not None else None,
        'customerName': data.get('customerName', ''),
        'ownerUid': data.get('ownerUid', ''),
        'ownerEmail': data.get('ownerEmail', ''),
        'ownerDisplayName': data.get('ownerDisplayName', data.get('customerName', '')),
        'hotdogName': data.get('hotdogName', ''),
        'unitPrice': float(data.get('unitPrice', 0.0)),
        'quantity': int(data.get('quantity', 1)),
        'notes': data.get('notes', ''),
        'status': data.get('status', 'pending'),
        'likes': int(data.get('likes', 0)),
        'likedBy': list(data.get('likedBy', [])),
        'messages': list(data.get('messages', [])),
        'createdAt': data.get('createdAt', ''),
        'updatedAt': data.get('updatedAt', ''),
    }


def get_all_orders():
    init_app()
    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.stream()
        return [_doc_to_order(d) for d in docs]

    # fallback
    return deepcopy(_in_memory_store)


def get_orders_for_user(user_uid, include_all=False):
    init_app()
    if include_all:
        return get_all_orders()

    if _use_firestore and _client is not None:
        coll = _client.collection('orders')
        docs = coll.where('ownerUid', '==', user_uid).stream()
        return [_doc_to_order(d) for d in docs]

    return [deepcopy(item) for item in _in_memory_store if item.get('ownerUid') == user_uid]


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
        now = datetime.now(timezone.utc).isoformat()
        payload.setdefault('likes', 0)
        payload.setdefault('likedBy', [])
        payload.setdefault('messages', [])
        payload.setdefault('createdAt', now)
        payload.setdefault('updatedAt', now)
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
    now = datetime.now(timezone.utc).isoformat()
    payload.setdefault('likes', 0)
    payload.setdefault('likedBy', [])
    payload.setdefault('messages', [])
    payload.setdefault('createdAt', now)
    payload.setdefault('updatedAt', now)
    _in_memory_store.append(payload)
    return deepcopy(payload)


def update_order(order_id, updates):
    init_app()
    updates = dict(updates)
    updates['updatedAt'] = datetime.now(timezone.utc).isoformat()
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


def toggle_order_like(order_id, user):
    order = get_order_by_id(order_id)
    if not order:
        return None

    liked_by = list(order.get('likedBy', []))
    user_uid = user.get('uid')
    if user_uid in liked_by:
        liked_by = [uid for uid in liked_by if uid != user_uid]
    else:
        liked_by.append(user_uid)

    return update_order(order_id, {'likedBy': liked_by, 'likes': len(liked_by)})


def add_order_message(order_id, user, message):
    order = get_order_by_id(order_id)
    if not order:
        return None

    messages = list(order.get('messages', []))
    messages.append({
        'authorUid': user.get('uid', ''),
        'authorLabel': user.get('displayName') or user.get('email') or 'Guest',
        'message': message,
        'createdAt': datetime.now(timezone.utc).isoformat(),
    })
    return update_order(order_id, {'messages': messages})


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

