#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "6061f659-9c9e-402a-8449-513f9f3d0341")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "Th08Q~SkKL9W31DOgzYs.G5z52S3KmbFT1gThbqs")
    API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:5005/api/bot")
