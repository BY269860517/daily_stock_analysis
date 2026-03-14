# -*- coding: utf-8 -*-
"""Tests for customers.json / CUSTOMERS_JSON configuration loading."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestCustomersConfig(unittest.TestCase):
    def setUp(self) -> None:
        from src.config import Config

        Config.reset_instance()

    def tearDown(self) -> None:
        from src.config import Config

        Config.reset_instance()

    @patch("src.config.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "CUSTOMERS_JSON": json.dumps(
                {
                    "customers": [
                        {"email": "user1@example.com", "stocks": ["aapl", "nvda"]},
                        {"email": "user2@example.com", "stocks": ["AAPL", "tsla"]},
                    ]
                }
            ),
            "STOCK_LIST": "MSFT",
        },
        clear=True,
    )
    def test_load_from_env_derives_stock_and_email_groups_from_customers_json(self, _mock_dotenv):
        from src.config import Config

        config = Config._load_from_env()

        self.assertEqual(config.customers_file, "CUSTOMERS_JSON")
        self.assertEqual(config.stock_list, ["AAPL", "NVDA", "TSLA", "MSFT"])
        self.assertEqual(
            config.stock_email_groups,
            [
                (["AAPL", "NVDA"], ["user1@example.com"]),
                (["AAPL", "TSLA"], ["user2@example.com"]),
            ],
        )

    @patch("src.config.load_dotenv")
    def test_load_from_env_reads_customers_file_relative_to_env_file(self, _mock_dotenv):
        from src.config import Config

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            env_path = base / ".env"
            env_path.write_text("", encoding="utf-8")
            customers_path = base / "customers.json"
            customers_path.write_text(
                json.dumps(
                    [
                        {"email": "alpha@example.com", "stocks": ["600519", "000001"]},
                        {
                            "emails": ["beta@example.com", "gamma@example.com"],
                            "stocks": "AAPL,TSLA",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "ENV_FILE": str(env_path),
                    "CUSTOMERS_FILE": "./customers.json",
                },
                clear=True,
            ):
                config = Config._load_from_env()

        self.assertEqual(config.customers_file, str(customers_path.resolve()))
        self.assertEqual(config.stock_list, ["600519", "000001", "AAPL", "TSLA"])
        self.assertEqual(
            config.stock_email_groups,
            [
                (["600519", "000001"], ["alpha@example.com"]),
                (["AAPL", "TSLA"], ["beta@example.com", "gamma@example.com"]),
            ],
        )

    @patch("src.config.load_dotenv")
    def test_refresh_stock_list_reloads_customer_file_groups(self, _mock_dotenv):
        from src.config import Config

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            env_path = base / ".env"
            env_path.write_text("CUSTOMERS_FILE=./customers.json\n", encoding="utf-8")
            customers_path = base / "customers.json"
            customers_path.write_text(
                json.dumps(
                    {"customers": [{"email": "user@example.com", "stocks": ["AAPL", "TSLA"]}]}
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"ENV_FILE": str(env_path)}, clear=True):
                config = Config(
                    stock_list=["000001"],
                    stock_email_groups=[(["000001"], ["legacy@example.com"])],
                )
                config.refresh_stock_list()

        self.assertEqual(config.customers_file, str(customers_path.resolve()))
        self.assertEqual(config.stock_list, ["AAPL", "TSLA"])
        self.assertEqual(
            config.stock_email_groups,
            [(["AAPL", "TSLA"], ["user@example.com"])],
        )


if __name__ == "__main__":
    unittest.main()
