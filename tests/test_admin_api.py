"""Tests for admin API routes."""
import pytest
from datetime import date, time, timedelta
from app import db
from app.models import Member, Block, BlockReason, Court


class TestGetBlocks:
    """Tests for getting blocks."""

    def test_get_blocks_requires_auth(self, client):
        """Should require authentication - redirects to login."""
        response = client.get('/api/admin/blocks/')
        # Session-based auth redirects to login page
        assert response.status_code in [302, 401]

    def test_get_blocks_requires_teamster_or_admin(self, client, test_member):
        """Should require teamster or admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/api/admin/blocks/')
        assert response.status_code == 403

    def test_get_blocks_success_admin(self, client, test_admin):
        """Admin should be able to get blocks."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/blocks/')
        assert response.status_code == 200
        data = response.get_json()
        assert 'blocks' in data


class TestCreateBlocks:
    """Tests for creating blocks."""

    def test_create_blocks_requires_auth(self, client):
        """Should require authentication - redirects to login."""
        response = client.post('/api/admin/blocks/', json={})
        # Session-based auth redirects to login page
        assert response.status_code in [302, 401]

    def test_create_blocks_requires_json(self, client, test_admin):
        """Should require JSON body."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/blocks/')
        # Flask returns 415 Unsupported Media Type when Content-Type is not application/json
        assert response.status_code in [400, 415]

    def test_create_blocks_requires_court_ids(self, client, test_admin, app):
        """Should require court_ids."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        with app.app_context():
            reason = BlockReason.query.first()
            reason_id = reason.id

        response = client.post('/api/admin/blocks/', json={
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'start_time': '10:00',
            'end_time': '12:00',
            'reason_id': reason_id
        })
        assert response.status_code == 400
        assert 'court_ids' in response.get_json()['error']

    def test_create_blocks_rejects_past_date(self, client, test_admin, app):
        """Should reject past dates."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        with app.app_context():
            reason = BlockReason.query.first()
            reason_id = reason.id

        response = client.post('/api/admin/blocks/', json={
            'court_ids': [1],
            'date': (date.today() - timedelta(days=1)).isoformat(),
            'start_time': '10:00',
            'end_time': '12:00',
            'reason_id': reason_id
        })
        assert response.status_code == 400
        assert 'vergangene' in response.get_json()['error']

    def test_create_blocks_success(self, client, test_admin, app):
        """Should create blocks successfully."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        with app.app_context():
            reason = BlockReason.query.first()
            reason_id = reason.id

        response = client.post('/api/admin/blocks/', json={
            'court_ids': [1, 2],
            'date': (date.today() + timedelta(days=5)).isoformat(),
            'start_time': '10:00',
            'end_time': '12:00',
            'reason_id': reason_id
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['block_count'] == 2


class TestDeleteBatch:
    """Tests for deleting block batches."""

    def test_delete_batch_requires_auth(self, client):
        """Should require authentication - redirects to login."""
        response = client.delete('/api/admin/blocks/some-batch-id')
        # Session-based auth redirects to login page
        assert response.status_code in [302, 401]

    def test_delete_batch_not_found(self, client, test_admin):
        """Should return 404 for non-existent batch."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.delete('/api/admin/blocks/non-existent-batch-id')
        assert response.status_code == 404


class TestPaymentDeadlineApi:
    """Tests for payment deadline API."""

    def test_get_payment_deadline_requires_admin(self, client, test_member):
        """Should require admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/api/admin/settings/payment-deadline')
        assert response.status_code == 403

    def test_get_payment_deadline_success(self, client, test_admin):
        """Admin should be able to get payment deadline."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/settings/payment-deadline')
        assert response.status_code == 200
        data = response.get_json()
        assert 'deadline' in data
        assert 'unpaid_count' in data

    def test_set_payment_deadline_requires_admin(self, client, test_member):
        """Should require admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.post('/api/admin/settings/payment-deadline', json={
            'deadline': (date.today() + timedelta(days=30)).isoformat()
        })
        assert response.status_code == 403

    def test_set_payment_deadline_success(self, client, test_admin):
        """Admin should be able to set payment deadline."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        deadline = (date.today() + timedelta(days=30)).isoformat()
        response = client.post('/api/admin/settings/payment-deadline', json={
            'deadline': deadline
        })
        assert response.status_code == 200

    def test_set_payment_deadline_invalid_date(self, client, test_admin):
        """Should reject invalid date format."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/settings/payment-deadline', json={
            'deadline': 'invalid-date'
        })
        assert response.status_code == 400

    def test_clear_payment_deadline(self, client, test_admin):
        """Admin should be able to clear payment deadline."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.delete('/api/admin/settings/payment-deadline')
        assert response.status_code == 200


class TestBlockReasons:
    """Tests for block reasons API."""

    def test_list_block_reasons_requires_teamster(self, client, test_member):
        """Should require teamster or admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/api/admin/block-reasons')
        assert response.status_code == 403

    def test_list_block_reasons_success(self, client, test_admin):
        """Should list block reasons for admin."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/block-reasons')
        assert response.status_code == 200
        data = response.get_json()
        assert 'reasons' in data
        assert len(data['reasons']) > 0

    def test_create_block_reason_requires_admin(self, client, app):
        """Should require admin role."""
        # Create a teamster
        with app.app_context():
            teamster = Member(
                firstname='Test',
                lastname='Teamster',
                email='teamster@example.com',
                role='teamster'
            )
            teamster.set_password('teamster123')
            db.session.add(teamster)
            db.session.commit()

        client.post('/auth/login', data={
            'email': 'teamster@example.com',
            'password': 'teamster123'
        })
        response = client.post('/api/admin/block-reasons', json={
            'name': 'New Reason'
        })
        assert response.status_code == 403

    def test_create_block_reason_success(self, client, test_admin):
        """Admin should be able to create block reasons."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/block-reasons', json={
            'name': 'Test Reason',
            'teamster_usable': True
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['reason']['name'] == 'Test Reason'

    def test_create_block_reason_missing_name(self, client, test_admin):
        """Should require name."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/block-reasons', json={
            'teamster_usable': True
        })
        assert response.status_code == 400

    def test_create_block_reason_duplicate_name(self, client, test_admin, app):
        """Should reject duplicate names."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        with app.app_context():
            existing_reason = BlockReason.query.first()
            existing_name = existing_reason.name

        response = client.post('/api/admin/block-reasons', json={
            'name': existing_name
        })
        assert response.status_code == 400
        assert 'existiert bereits' in response.get_json()['error']

    def test_update_block_reason_success(self, client, test_admin, app):
        """Admin should be able to update block reasons."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        with app.app_context():
            reason = BlockReason.query.first()
            reason_id = reason.id

        response = client.put(f'/api/admin/block-reasons/{reason_id}', json={
            'teamster_usable': True
        })
        assert response.status_code == 200

    def test_delete_block_reason_success(self, client, test_admin, app):
        """Admin should be able to delete unused block reasons."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })

        # Create a new reason to delete
        response = client.post('/api/admin/block-reasons', json={
            'name': 'Reason To Delete'
        })
        reason_id = response.get_json()['reason']['id']

        response = client.delete(f'/api/admin/block-reasons/{reason_id}')
        assert response.status_code == 200


class TestConflictPreview:
    """Tests for conflict preview endpoint."""

    def test_conflict_preview_requires_auth(self, client):
        """Should require authentication."""
        response = client.post('/api/admin/blocks/conflict-preview', json={})
        assert response.status_code == 401

    def test_conflict_preview_requires_fields(self, client, test_admin):
        """Should require all fields."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/blocks/conflict-preview', json={})
        assert response.status_code == 400

    def test_conflict_preview_success(self, client, test_admin):
        """Should return conflict preview."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.post('/api/admin/blocks/conflict-preview', json={
            'court_ids': [1],
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'start_time': '10:00',
            'end_time': '12:00'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'conflicts' in data
        assert 'conflict_count' in data


class TestAuditLog:
    """Tests for audit log endpoint."""

    def test_audit_log_requires_admin(self, client, test_member):
        """Should require admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/api/admin/blocks/audit-log')
        assert response.status_code == 403

    def test_audit_log_success(self, client, test_admin):
        """Admin should be able to view audit log."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/blocks/audit-log')
        assert response.status_code == 200
        data = response.get_json()
        assert 'logs' in data

    def test_audit_log_filter_by_type(self, client, test_admin):
        """Should filter by log type."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/blocks/audit-log?type=block')
        assert response.status_code == 200

    def test_audit_log_limit(self, client, test_admin):
        """Should respect limit parameter."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/blocks/audit-log?limit=10')
        assert response.status_code == 200


class TestChangelog:
    """Tests for changelog endpoint."""

    def test_changelog_requires_admin(self, client, test_member):
        """Should require admin role."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/api/admin/changelog')
        assert response.status_code == 403

    def test_changelog_success(self, client, test_admin):
        """Admin should be able to view changelog."""
        client.post('/auth/login', data={
            'email': test_admin.email,
            'password': 'admin123'
        })
        response = client.get('/api/admin/changelog')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
