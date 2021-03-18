import json
import os
from pathlib import Path
from unittest.mock import Mock
import asyncio
import websockets
import pytest
from ert_shared.ensemble_evaluator.entity.ensemble import (
    create_ensemble_builder,
    create_legacy_job_builder,
    create_legacy_stage_builder,
    create_realization_builder,
    create_step_builder,
)
from res.enkf import ConfigKeys
from res.enkf.queue_config import QueueConfig
from res.job_queue.driver import LOCAL_DRIVER
from res.job_queue.ext_job import ExtJob


@pytest.fixture
def queue_config():
    return QueueConfig(
        config_dict={
            ConfigKeys.JOB_SCRIPT: "job_dispatch.py",
            ConfigKeys.USER_MODE: True,
            ConfigKeys.MAX_SUBMIT: 100,
            ConfigKeys.NUM_CPU: 10,
            ConfigKeys.QUEUE_SYSTEM: LOCAL_DRIVER,
            ConfigKeys.QUEUE_OPTION: [
                {ConfigKeys.NAME: "MAX_RUNNING", ConfigKeys.VALUE: "50"}
            ],
        }
    )


@pytest.fixture
def make_ensemble_builder(queue_config):
    def _make_ensemble_builder(tmpdir, num_reals, num_jobs):
        builder = create_ensemble_builder()
        with tmpdir.as_cwd():
            ext_job_list = []
            for job_index in range(0, num_jobs):
                ext_job_config = Path(tmpdir) / f"EXT_JOB_{job_index}"
                with open(ext_job_config, "w") as f:
                    f.write(f"EXECUTABLE ext_{job_index}.py\n")

                ext_job_exec = Path(tmpdir) / f"ext_{job_index}.py"
                with open(ext_job_exec, "w") as f:
                    f.write(
                        "#!/usr/bin/env python\n"
                        'if __name__ == "__main__":\n'
                        f'    print("stdout from {job_index}")\n'
                    )

                ext_job_list.append(
                    ExtJob(str(ext_job_config), False, name=f"ext_job_{job_index}")
                )

            for iens in range(0, num_reals):
                run_path = Path(tmpdir / f"real_{iens}")
                os.mkdir(run_path)

                with open(run_path / "jobs.json", "w") as f:
                    json.dump(
                        {
                            "jobList": [
                                _dump_ext_job(ext_job, index)
                                for index, ext_job in enumerate(ext_job_list)
                            ],
                            "umask": "0022",
                        },
                        f,
                    )

                step = create_step_builder().set_id(0).set_dummy_io()

                for index, job in enumerate(ext_job_list):
                    step.add_job(
                        create_legacy_job_builder()
                        .set_id(index)
                        .set_name(f"dummy job {index}")
                        .set_ext_job(job)
                    )

                builder.add_realization(
                    create_realization_builder()
                    .active(True)
                    .set_iens(iens)
                    .add_stage(
                        create_legacy_stage_builder()
                        .set_id(0)
                        .set_job_name("some_stage")
                        .set_job_script("job_dispatch.py")
                        .set_status("Unknown")
                        .set_max_runtime(10000)
                        .set_run_arg(Mock(iens=iens))
                        .set_done_callback(lambda _: True)
                        .set_exit_callback(lambda _: True)
                        # the first callback_argument is expected to be a run_arg
                        # from the run_arg, the queue wants to access the iens prop
                        .set_callback_arguments([])
                        .set_run_path(str(run_path))
                        .add_step(step)
                    )
                )

        analysis_config = Mock()
        analysis_config.get_stop_long_running = Mock(return_value=False)

        ecl_config = Mock()
        ecl_config.assert_restart = Mock()

        builder.set_legacy_dependencies(
            queue_config,
            analysis_config,
        )
        return builder

    return _make_ensemble_builder


def _dump_ext_job(ext_job, index):
    return {
        "name": ext_job.name(),
        "executable": ext_job.get_executable(),
        "target_file": ext_job.get_target_file(),
        "error_file": ext_job.get_error_file(),
        "start_file": ext_job.get_start_file(),
        "stdout": f"{index}.stdout",
        "stderr": f"{index}.stderr",
        "stdin": ext_job.get_stdin_file(),
        "license_path": ext_job.get_license_path(),
        "environment": None,
        "exec_env": {},
        "max_running": ext_job.get_max_running(),
        "max_running_minutes": ext_job.get_max_running_minutes(),
        "min_arg": ext_job.min_arg,
        "max_arg": ext_job.max_arg,
        "arg_types": ext_job.arg_types,
        "argList": ext_job.get_arglist(),
    }


def _mock_ws(host, port, messages, delay_startup=0):
    loop = asyncio.new_event_loop()
    done = loop.create_future()

    async def _handler(websocket, path):
        while True:
            msg = await websocket.recv()
            messages.append(msg)
            if msg == "stop":
                done.set_result(None)
                break

    async def _run_server():
        await asyncio.sleep(delay_startup)
        async with websockets.serve(_handler, host, port):
            await done

    loop.run_until_complete(_run_server())
    loop.close()
