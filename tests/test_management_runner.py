import io
import os.path

from django.db import connection

from django_north.management.runner import Block
from django_north.management.runner import MetaBlock
from django_north.management.runner import Script
from django_north.management.runner import SimpleBlock


def test_script_init(settings):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')

    # Simple script
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '16.12/16.12-0-version-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1
    assert isinstance(script.block_list[0], SimpleBlock) is True

    # Manual script without metablocks
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/manual/17.01-feature_a-070-dl.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1
    assert isinstance(script.block_list[0], SimpleBlock) is False
    assert isinstance(script.block_list[0], Block) is True

    # Manual script with metablocks
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/manual/17.01-feature_a-040-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 3
    assert isinstance(script.block_list[0], SimpleBlock) is False
    assert isinstance(script.block_list[0], Block) is True
    assert isinstance(script.block_list[1], MetaBlock) is True
    assert isinstance(script.block_list[2], SimpleBlock) is False
    assert isinstance(script.block_list[2], Block) is True

    # Manual script not in 'manual' subdirectory
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.02/17.02-feature_b_manual-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 3
    assert isinstance(script.block_list[0], SimpleBlock) is False
    assert isinstance(script.block_list[0], Block) is True
    assert isinstance(script.block_list[1], MetaBlock) is True
    assert isinstance(script.block_list[2], SimpleBlock) is False
    assert isinstance(script.block_list[2], Block) is True

    # None manual script not in 'manual' subdirectory
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.02/17.02-feature_c_fakemanual-ddl.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1
    assert isinstance(script.block_list[0], SimpleBlock) is True

    # Non manual script but it contains 'CONCURRENTLY' keyword
    settings.NORTH_NON_TRANSACTIONAL_KEYWORDS = ['CONCURRENTLY']
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/17.01-feature_b-ddl.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1
    assert isinstance(script.block_list[0], SimpleBlock) is False
    assert isinstance(script.block_list[0], Block) is True

    # Non manual script but 'CONCURRENTLY' is not a keyword
    settings.NORTH_NON_TRANSACTIONAL_KEYWORDS = []
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/17.01-feature_b-ddl.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1
    assert isinstance(script.block_list[0], SimpleBlock) is True


def test_simple_script_run(settings, mocker):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')

    mock_simple_run = mocker.patch(
        'django_north.management.runner.SimpleBlock.run')
    mock_run = mocker.patch('django_north.management.runner.Block.run')
    mock_meta_run = mocker.patch(
        'django_north.management.runner.MetaBlock.run')
    mock_discard_run = mocker.patch(
        'django_north.management.runner.DiscardBlock.run')

    # Simple script
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '16.12/16.12-0-version-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1

    script.run('foo')
    assert mock_simple_run.call_args_list == [mocker.call('foo')]
    assert mock_run.called is False
    assert mock_meta_run.called is False
    assert mock_discard_run.called is True


def test_simple_script_run_no_discard(settings, mocker):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')
    settings.NORTH_DISCARD_ALL = False

    mock_simple_run = mocker.patch(
        'django_north.management.runner.SimpleBlock.run')
    mock_run = mocker.patch('django_north.management.runner.Block.run')
    mock_meta_run = mocker.patch(
        'django_north.management.runner.MetaBlock.run')
    mock_discard_run = mocker.patch(
        'django_north.management.runner.DiscardBlock.run')

    # Simple script
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '16.12/16.12-0-version-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1

    script.run('foo')
    assert mock_simple_run.call_args_list == [mocker.call('foo')]
    assert mock_run.called is False
    assert mock_meta_run.called is False
    # The most important result here: we don't run the discard command.
    assert mock_discard_run.called is False


def test_manual_script_run(settings, mocker):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')

    mock_simple_run = mocker.patch(
        'django_north.management.runner.SimpleBlock.run')
    mock_run = mocker.patch('django_north.management.runner.Block.run')
    mock_meta_run = mocker.patch(
        'django_north.management.runner.MetaBlock.run')
    mock_discard_run = mocker.patch(
        'django_north.management.runner.DiscardBlock.run')

    # Manual script with metablocks
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/manual/17.01-feature_a-040-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 3

    script.run('foo')
    assert mock_simple_run.called is False
    assert mock_run.call_args_list == [mocker.call('foo'), mocker.call('foo')]
    assert mock_meta_run.call_args_list == [mocker.call('foo')]
    assert mock_discard_run.called is True


def test_block_run(settings, mocker):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')

    cursor = mocker.MagicMock(rowcount=0)
    mock_cursor = mocker.patch('django.db.connection.cursor')
    mock_cursor.return_value.__enter__.return_value = cursor

    # Simple script
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '16.12/16.12-0-version-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 1

    block = script.block_list[0]
    block.run(connection)
    # comment + instruction
    # last comment is ignored
    assert len(cursor.execute.call_args_list) == 1

    cursor.execute.reset_mock()
    cursor.rowcount = 0

    # Manual script with metablocks
    path = os.path.join(settings.NORTH_MIGRATIONS_ROOT,
                        '17.01/manual/17.01-feature_a-040-dml.sql')
    with io.open(path, 'r', encoding='utf8') as f:
        script = Script(f)
    assert len(script.block_list) == 3

    # execute until rowcount == 0
    mock_run = mocker.patch(
        'django_north.management.runner.Block.run',
        side_effect=[500, 299, 0])
    meta_block = script.block_list[1]
    meta_block.run(connection)
    # block executed 3 times
    assert len(mock_run.call_args_list) == 3
