import importlib.util
import os
from collections import defaultdict
from pathlib import Path
import pytest
from airflow import DAG


@pytest.fixture
def dags(dagbag):
    return dagbag.dags.values()


def is_error(error, error_string):
    # The error messages in Airflow 1.8 look like "u'Error message'", so we
    # clean them before checking what they are.
    error = error.strip("u'")
    return error.startswith(error_string)


@pytest.mark.usefixtures('disable_airflow_logger')
def test_imports(dagbag):
    """Verify no unexpected errors when importing dags"""
    valid_errs = [

    ]
    import_errors = [
        (error, path) for path, error in dagbag.import_errors.items()
        if not any([is_error(error, i) for i in valid_errs])
    ]
    assert not import_errors


def test_dagbag_import_time(dagbag):
    """Verify that files describing DAGs load fast enough"""
    threshold = 4  # seconds
    slow_files = [i for i in dagbag.dagbag_stats if i.duration > threshold]
    slow_fnames = [i.file[1:] for i in slow_files]
    msg = f'The following files took more than {threshold}s to load: {slow_fnames}'
    assert not slow_fnames, msg


def test_start_dates_are_set_to_constant_values(dags):
    # This doesn't guarantee the time isn't set to `utcnow()` or similar,
    # but is a close approximate.
    is_static_time = lambda time: time.microsecond == 0  # noqa: E731

    for dag in dags:
        for task in dag.tasks:
            start_date = task.start_date
            if start_date:
                msg = (
                    f'You should always set the "start_date" to a static'
                    f' time (DAG: {task.dag_id}, task: {task.task_id}).'
                )
                assert is_static_time(start_date), msg


def test_alert_email_present(dags):
    for dag in dags:
        if any([dag.default_args.get(i)
                for i in ('email_on_failure', 'email_on_retry')]):
            emails = dag.default_args.get('email', [])
            msg = 'Alert email not set for DAG {id}'.format(id=dag.dag_id)
            assert 'airflow@juvo.com' in emails, msg


def test_at_least_one_task(dags):
    for dag in dags:
        assert len(dag.tasks) == 1, dag


class TestRawFiles:
    @pytest.fixture(scope='module')
    def raw_dags(self, this_repo):
        dags_path = this_repo.joinpath('dags')
        dags = []
        for region in dags_path.iterdir():
            for filename in region.glob('**/*.py'):
                spec = importlib.util.spec_from_file_location('dag', filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                dags.append((str(region), filename, module))
        return dags

    def test_dags_are_dags(self, raw_dags):
        for _, fpath, module in raw_dags:
            msg = f"{fpath} missing dag"
            assert any(
                isinstance(var, DAG)
                for var in vars(module).values()
            ), msg

    def test_dags_have_unique_ids(self, raw_dags):
        seen_ids = defaultdict(dict)
        for region, fpath, module in raw_dags:
            for var in vars(module).values():
                if isinstance(var, DAG):
                    id_ = var.dag_id
                    msg = f'Duplicate DAG id `{id_}` found: ({fpath}, {seen_ids[region].get(id_)})'
                    assert id_ not in seen_ids[region], msg
                    seen_ids[region][id_] = fpath
