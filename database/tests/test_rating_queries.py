"""Run with database/venv/bin/python -m unittest discover -s database/tests.

Load calculation definitions without importing route startup hooks, which connect
and load production data at import time. SQL execution is mocked throughout.
"""
import ast
import math
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import peewee

ROOT = Path(__file__).resolve().parents[1]


def definitions(path, names, env):
    tree = ast.parse((ROOT / path).read_text())
    nodes = []
    for node in tree.body:
        if getattr(node, 'name', None) in names or (
            isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in names for t in node.targets)):
            if hasattr(node, 'decorator_list'):
                node.decorator_list = []
            nodes.append(node)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return env


def environment():
    env = dict(vars(peewee), BaseModel=peewee.Model, time=time, math=math)
    definitions('models/base.py', {'Player'}, env)
    definitions('models/maimai.py', {'SCORE_COEFFICIENT_TABLE', 'ScoreCoefficient'}, env)
    return env


class RatingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = environment()
        self.Player = self.env['Player']
        self.player = self.Player(id=7, rating=100, maimai_new_rating=20,
                                 maimai_legacy_count=35, maimai_new_count=15,
                                 access_time=990, chuni_new_rating=2, chuni_rating=10)
        self.query = Mock()
        self.query.where.return_value.aio_execute = AsyncMock(return_value=1)
        self.update = patch.object(self.Player, 'update', return_value=self.query).start()
        self.addCleanup(patch.stopall)
        patch('time.time', return_value=1000).start()

    async def test_unchanged_does_not_write(self):
        await self.player.update_rating(rating=100, maimai_new_rating=20)
        self.update.assert_not_called()

    async def test_changes_only_write_changed_columns(self):
        await self.player.update_rating(rating=120, maimai_new_rating=20)
        self.update.assert_called_once_with(rating=120, access_time=1000)
        self.assertEqual(self.player.rating, 120)

    async def test_old_access_time_only_touches_timestamp(self):
        self.player.access_time = 700
        await self.player.update_rating(rating=100)
        self.update.assert_called_once_with(access_time=1000)

    async def test_integer_storage_does_not_cause_repeated_chuni_writes(self):
        await self.player.update_rating(chuni_new_rating=2.75, chuni_rating=10)
        self.update.assert_not_called()

    def maimai(self):
        self.env['NewRecord'] = Mock()
        return definitions('routes/maimai.py',
                           {'get_dx_and_sd', 'get_dx_and_sd_for50', 'compute_ra'}, self.env)

    async def test_empty_records_reset_rating_without_select(self):
        env = self.maimai()
        await env['compute_ra'](self.player, records=[])
        env['NewRecord'].raw.assert_not_called()
        self.assertEqual(self.player.rating, 0)
        self.assertEqual(self.player.maimai_legacy_count, 0)

    async def test_reuse_preserves_b40_b50_limits_order_and_utage_rule(self):
        env = self.maimai()
        records = [SimpleNamespace(id=i, achievements=100 + (i % 3)*.1,
                                   ds=10 + (i % 10)*.1, is_new=i >= 45)
                   for i in range(75)]
        records += [SimpleNamespace(id=100000, achievements=100.5, ds=15, is_new=False)]
        before = list(records)
        b40 = await env['get_dx_and_sd'](self.player, records=records)
        b50 = await env['get_dx_and_sd_for50'](self.player, records=records)
        self.assertEqual([len(x) for x in b40], [25, 15])
        self.assertEqual([len(x) for x in b50], [35, 15])
        self.assertEqual(b40[0][0].id, 100000)
        expected = sorted([r for r in records if not r.is_new and r.id < 100000],
                          key=lambda r: (r.ra, r.ds, r.achievements), reverse=True)[:35]
        self.assertEqual(b50[0], expected)
        await env['compute_ra'](self.player, records=records)
        self.assertEqual(self.player.rating, sum(r.ra for group in b50 for r in group))
        env['NewRecord'].raw.assert_not_called()
        self.assertEqual(records, before)

    async def test_write_callers_still_fetch_when_no_records_supplied(self):
        env = self.maimai()
        env['NewRecord'].raw.return_value.aio_execute = AsyncMock(return_value=[])
        await env['compute_ra'](self.player)
        env['NewRecord'].raw.return_value.aio_execute.assert_awaited_once()

    async def test_chuni_reuses_records_and_precomputed_best(self):
        env = dict(self.env, ChuniRecord=Mock(), single_ra=lambda r:r.score,
                   latest_version=['new'], chart_id_map={1:(0,{'basic_info':{'from':'old'}}),
                                                        2:(0,{'basic_info':{'from':'new'}})})
        definitions('routes/chunithm.py', {'get_b50','compute_ra'}, env)
        records = [SimpleNamespace(chart_id=1,score=10), SimpleNamespace(chart_id=2,score=15)]
        old, new = await env['get_b50'](self.player, records=records)
        result = await env['compute_ra'](self.player, old30=old, new20=new)
        self.assertEqual(result, .5)
        env['ChuniRecord'].raw.assert_not_called()
        await env['compute_ra'](self.player, records=[])
        self.assertEqual(self.player.chuni_rating, 0)


if __name__ == '__main__':
    unittest.main()
