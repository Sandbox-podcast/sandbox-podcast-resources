from __future__ import annotations

import os
from contextlib import closing
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from youtube_growth.core import ReplyDecision, State
from youtube_growth.identity import SANDBOX_CHANNEL_ID
from youtube_growth.pipeline import _process_new_comments, run_poll
from youtube_growth.shorts import upload_once
from youtube_growth.storage import Journal


class PipelineJournalTests(unittest.TestCase):
    def test_poll_without_durable_storage_blocks_before_any_network_action(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'YOUTUBE_EXECUTE_ACTIONS': 'true',
                                    'YOUTUBE_INITIAL_REVIEW_CONFIRMED': 'true', 'YOUTUBE_JOURNAL_DATABASE_URL': ''}):
            with patch('youtube_growth.youtube_api.build_youtube_service') as service:
                with self.assertRaises(RuntimeError):
                    run_poll()
                service.assert_not_called()

    def test_replayed_poll_cannot_post_a_second_reply_even_with_a_different_ai_text(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory, closing(Journal(Path(directory) / 'operations.sqlite3')) as journal:
            thread = {'id': 'thread', 'snippet': {'canReply': True, 'totalReplyCount': 0, 'videoId': 'v',
                      'topLevelComment': {'id': 'parent', 'snippet': {'textOriginal': 'Bonjour', 'authorChannelId': {'value': 'viewer'}}}}}
            with patch.dict(os.environ, {'YOUTUBE_AUTO_REPLY': 'true'}), \
                 patch('youtube_growth.pipeline.list_recent_comment_threads', return_value=[thread]), \
                 patch('youtube_growth.pipeline.generate_reply', side_effect=[ReplyDecision(True, 'Merci', ''), ReplyDecision(True, 'Merci beaucoup', '')]), \
                 patch('youtube_growth.pipeline.post_reply', return_value='published') as post:
                for _ in range(2):
                    _process_new_comments(Mock(), SANDBOX_CHANNEL_ID, {'v': {'id': 'v'}}, State(comments_baselined=True), [], True, journal)
                self.assertEqual(post.call_count, 1)


class UploadOnceTests(unittest.TestCase):
    def setUp(self):
        # Only the journal behavior is exercised; _upload_clip is a local mock.
        # The unpatched entry point must reject writes in test_factory_connectors.
        self.enterContext(patch('youtube_growth.factory.connectors.guard_legacy_write'))

    def test_upload_recovers_committed_id_without_reuploading_changed_metadata(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            clip = Path(directory) / 'clip.mp4'
            clip.write_bytes(b'test-media')
            with patch.dict(os.environ, {'GITHUB_ACTIONS': '', 'YOUTUBE_JOURNAL_DATABASE_URL': ''}), \
                 patch('youtube_growth.shorts._upload_clip', return_value='abcdefghijk') as upload:
                self.assertEqual(upload_once(Mock(), clip, {'title': 'Premier titre'}, 'Episode', 'source'), 'abcdefghijk')
                self.assertEqual(upload_once(Mock(), clip, {'title': 'Autre titre'}, 'Episode', 'source'), 'abcdefghijk')
                self.assertEqual(upload.call_count, 1)
