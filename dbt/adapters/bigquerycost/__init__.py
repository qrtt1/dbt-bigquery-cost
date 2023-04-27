import copy

from dbt.adapters.bigquery import BigQueryCredentials
from dbt.contracts.connection import Credentials

from dbt.adapters.bigquerycost.connections import BigQueryCostConnectionManager  # noqa
from dbt.adapters.bigquerycost.connections import BigQueryCostCredentials
from dbt.adapters.bigquerycost.impl import BigQueryCostAdapter

from dbt.adapters.base import AdapterPlugin
from dbt.include import bigquery, bigquerycost

from dbt.adapters.factory import FACTORY

FACTORY.origin_load_plugin = FACTORY.load_plugin


class HackedAdapterPlugin(AdapterPlugin):
    def __init__(
            self,
            adapter,
            credentials,
            include_path: str,
            dependencies=None
    ):
        super().__init__(adapter, credentials, include_path, dependencies)

    def __getattribute__(self, item):
        # print("XXX", item)
        if item == "credentials":
            FACTORY.load_plugin("bigquery")
            FACTORY.load_plugin("bigquery")
            FACTORY.plugins['bigquerycost'] = FACTORY.plugins['bigquery']
        return super().__getattribute__(item)


Plugin = HackedAdapterPlugin(
    adapter=BigQueryCostAdapter,
    credentials=BigQueryCredentials,
    include_path=bigquery.PACKAGE_PATH
)

from dbt.adapters.bigquery.connections import BigQueryConnectionManager

BigQueryConnectionManager.origin_open = BigQueryConnectionManager.open


def x(cls, connection):
    connection = BigQueryConnectionManager.origin_open(connection)
    # print("XXX", connection)
    # print("XXX_", connection.handle)
    # help(connection.handle.query)

    connection.handle.origin_query = connection.handle.query

    def q(query: str, **kwargs):
        # print(kwargs)
        from google.cloud.bigquery.job.query import QueryJobConfig
        dry_run_args = copy.deepcopy(kwargs)
        job: QueryJobConfig = dry_run_args['job_config']
        job.dry_run = True

        query_job = connection.handle.origin_query(query, **dry_run_args)
        print("This query will process {} bytes.".format(query_job.total_bytes_processed))

        return connection.handle.origin_query(query, **kwargs)

    connection.handle.query = q

    return connection


BigQueryConnectionManager.open = x
