from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from youtube_growth.core import State
from youtube_growth.storage import Journal, execute_once, open_journal


class JournalTests(unittest.TestCase):
    def test_changed_generated_text_cannot_duplicate_a_reply_after_losing_state(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / 'journal.sqlite3'
            action = Mock(return_value='comment-id')
            journal = Journal(path)
            self.assertTrue(execute_once(journal, 'reply', {'parent': 'p'}, {'text': 'Merci'}, action))
            journal.close()
            journal = Journal(path)
            self.assertFalse(execute_once(journal, 'reply', {'parent': 'p'}, {'text': 'Autre rÃ©ponse'}, action))
            journal.close()
            self.assertEqual(action.call_count, 1)

    def test_uncertain_write_stays_blocked_after_restart(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / 'journal.sqlite3'
            journal = Journal(path)
            with self.assertRaises(TimeoutError):
                execute_once(journal, 'reply', {'parent': 'p'}, {}, Mock(side_effect=TimeoutError))
            journal.close()
            journal = Journal(path)
            action = Mock()
            with self.assertRaises(RuntimeError):
                execute_once(journal, 'reply', {'parent': 'p'}, {}, action)
            action.assert_not_called()
            journal.close()

    def test_ci_never_falls_back_to_local_cache(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'YOUTUBE_JOURNAL_DATABASE_URL': ''}):
            with self.assertRaisesRegex(RuntimeError, 'YOUTUBE_JOURNAL_DATABASE_URL'):
                open_journal(Path('unused.sqlite3'))

    def test_insecure_or_pooled_database_is_rejected_before_connecting(self):
        for url in ['https://example.test', 'postgresql://user:secret@remote.test/db',
                    'postgresql://user:secret@ep-test-pooler.neon.tech/db?sslmode=require']:
            with self.subTest(url=url), patch.dict(os.environ, {'YOUTUBE_JOURNAL_DATABASE_URL': url}):
                with self.assertRaises(RuntimeError):
                    open_journal(Path('unused.sqlite3'))


@unittest.skipUnless(os.environ.get('YOUTUBE_TEST_DATABASE_URL'), 'Base Postgres de test non configurÃ©e')
class PostgresJournalTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        from psycopg import sql
        from uuid import uuid4
        self.url = os.environ['YOUTUBE_TEST_DATABASE_URL']
        connection_info = conninfo_to_dict(self.url)
        if connection_info.get('host') not in {'localhost', '127.0.0.1', '::1'}:
            self.fail('Ces tests crÃ©ent un schÃ©ma uniquement sur une base locale Ã©phÃ©mÃ¨re.')
        self.schema = 'test_journal_' + uuid4().hex
        self.connection = psycopg.connect(self.url, autocommit=True)
        self.connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
        self.connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
        self.connection.execute((Path(__file__).resolve().parents[1] / 'sql/001_durable_journal.sql').read_text())
        self.addCleanup(self.connection.close)
        self.addCleanup(lambda: self.connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema))))

    def journal(self):
        from psycopg import sql
        from youtube_growth.postgres_storage import PostgresJournal
        # Constructor checks tables before search_path can be selected: use a scoped PGOPTIONS.
        import psycopg
        original = psycopg.connect
        def connect(*args, **kwargs):
            kwargs['options'] = f'-c search_path={self.schema} -c statement_timeout=15000'
            return original(*args, **kwargs)
        with patch('psycopg.connect', side_effect=connect):
            journal = PostgresJournal(self.url)
        self.addCleanup(journal.close)
        return journal

    def test_restart_preserves_state_completed_intents_and_uncertain_writes(self):
        first = self.journal()
        first.save_state(State(last_video_id='source', comments_baselined=True))
        operation, allowed = first.begin('reply', {'text': 'Merci'}, {'parent': 'p'})
        self.assertTrue(allowed)
        first.finish(operation, {'id': 'remote-id'})
        first.begin('reply', {'text': 'Incertain'}, {'parent': 'other'})
        first.close()
        second = self.journal()
        self.assertEqual(second.load_state().last_video_id, 'source')
        self.assertFalse(second.begin('reply', {'text': 'ReformulÃ©'}, {'parent': 'p'})[1])
        with self.assertRaises(RuntimeError):
            second.begin('reply', {'text': 'Incertain'}, {'parent': 'other'})

    def test_two_connections_reserve_the_same_intent_once(self):
        from concurrent.futures import ThreadPoolExecutor
        first, second = self.journal(), self.journal()
        def reserve(journal):
            try:
                return journal.begin('upload', {'video': 'source'})[1]
            except RuntimeError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(reserve, [first, second])), [False, True])
        with first.exclusive_poll():
            with self.assertRaises(RuntimeError):
                with second.exclusive_poll():
                    self.fail('Deux pollings actifs')
        with second.exclusive_poll():
            self.assertEqual(second.load_state(), State())

    def test_invalid_remote_state_fails_closed(self):
        from youtube_growth.identity import expected_channel_id
        self.connection.execute('INSERT INTO youtube_poll_state VALUES (%s,%s::jsonb,now())',
                                (expected_channel_id(), '{"comments_baselined":"yes"}'))
        with self.assertRaises(ValueError):
            self.journal().load_state()
