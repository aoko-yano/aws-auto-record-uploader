from unittest.mock import MagicMock

from aws_auto_record_uploader import cli


def test_main_passes_cli_config_to_run_pipeline(monkeypatch):
    run_pipeline_mock = MagicMock()
    monkeypatch.setattr("aws_auto_record_uploader.cli.run_pipeline", run_pipeline_mock)
    monkeypatch.setattr("sys.argv", ["aws-auto-record-uploader", "--config", "custom.json"])

    cli.main()

    run_pipeline_mock.assert_called_once_with("custom.json")
